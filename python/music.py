import json
import os
from functools import partial
from tqdm import tqdm
import aiofiles
from aiohttp import ClientSession
import re
import asyncio


# 判断是多集还是单集
async def fast(url, headers, file_headers):
    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            html = await response.text()
            p = '视频选集'
            tasks = []
            if re.search(p, html):
                parten = 'part'
                result_parten = re.findall(parten, html)
                for num in range(1, len(result_parten) + 1):
                    every_pageurl = url + '?p=' + str(num)
                    videouUrl, audioUrl, name = await get_baseurl(every_pageurl, session, headers)
                    task = asyncio.ensure_future(download(videouUrl, audioUrl, session, name, headers=file_headers))
                    tasks.append(task)
                await asyncio.gather(*tasks)

            else:
                videouUrl, audioUrl, name = await get_baseurl(url, session, headers)
                await download(videouUrl, audioUrl, session, name, headers=file_headers)


# 获取资源baseurl
async def get_baseurl(url, session, headers):
    async with session.get(url, headers=headers) as response:
        html = await response.text()
        urlData = json.loads(re.findall('<script>window.__playinfo__=(.*?)</script>', html, re.M)[0])
        videoUrl = urlData['data']['dash']['video'][0]['baseUrl']
        audioUrl = urlData['data']['dash']['audio'][0]['baseUrl']
        name = re.findall('<h1 title="(.*?)" class="video-title">', html, re.M)[0]
        return videoUrl, audioUrl, name


async def download(videourl, audiourl, session, name, headers):
    video_official_filename = name + '.m4s'
    video_temp_filename = video_official_filename + '.tem'
    video_config_filename = video_official_filename + '.cfg'

    audio_official_filename = name + '.mp3'
    audio_temp_filename = audio_official_filename + '.tem'
    audio_config_filename = audio_official_filename + '.cfg'

    if os.path.exists(video_official_filename) and os.path.exists(audio_official_filename):
        print(f'{name}整体文件已下载')
    elif not os.path.exists(video_official_filename) and os.path.exists(audio_official_filename):
        print(f'{audio_official_filename}' + f'已下载，即将下载{name}视频文件')
        if os.path.exists(video_temp_filename):
            await get_videopart(videourl, session, headers, video_temp_filename, video_config_filename,
                                video_official_filename)
        else:
            await get_video(videourl, session, name, headers)

    elif not os.path.exists(audio_official_filename) and os.path.exists(video_official_filename):
        print(f'{video_official_filename}' + f'已下载，即将下载{name}音频文件')
        if os.path.exists(audio_temp_filename):
            await get_audiopart(audiourl, session, headers, audio_temp_filename, audio_config_filename,
                                audio_official_filename)
        else:
            await get_audio(videourl, session, name, headers)

    elif (not os.path.exists(audio_temp_filename)) and (not os.path.exists(video_temp_filename)):
        print('未下载，启动下载程序')
        print(headers)

        # await get_video( videourl, session, name, headers)
        #
        # await get_audio(audiourl, session, name, headers)
        await asyncio.gather(get_video(videourl, session, name, headers), get_audio(audiourl, session, name, headers))

    elif os.path.exists(video_temp_filename) and os.path.exists(audio_temp_filename):
        await asyncio.gather(get_videopart(videourl, session, headers, video_temp_filename, video_config_filename,
                                           video_official_filename),
                             get_audiopart(audiourl, session, headers, audio_temp_filename, audio_config_filename,
                                           audio_official_filename))


async def get_videopart(videourl, session, headers, video_temp_filename, video_config_filename,
                        video_official_filename):
    async with aiofiles.open(video_config_filename, 'r') as fp:
        all_fp = await fp.read()
    cfg = json.loads(all_fp)
    succeed_parts = {part['PartNumber'] for part in cfg['successparts']}  # 之前已下载好的分块号集合
    succeed_parts_size = sum([part['Size'] for part in cfg['successparts']])  # 已下载的块的总大小
    parts = set(cfg['partnums']) - succeed_parts  # 本次需要下载的分块号集合
    video_size = cfg['size']
    parts_count = cfg['parts_count']
    await get_file(videourl, session, headers, parts_count, video_temp_filename, video_config_filename,
                   video_official_filename, video_size, parts, succeed_parts_size)


async def get_audiopart(audiourl, session, headers, audio_temp_filename, audio_config_filename,
                        audio_official_filename):
    async with aiofiles.open(audio_config_filename, 'r') as f:
        all_f = await f.read()
    audio_cfg = json.loads(all_f)
    audio_succeed_parts = {audio_part['PartNumber'] for audio_part in audio_cfg['successparts']}
    audio_succeed_parts_size = sum([audio_part['Size'] for audio_part in audio_cfg['successparts']])
    audio_parts = set(audio_cfg['partnums']) - audio_succeed_parts
    audio_audio_size = audio_cfg['size']
    audio_parts_count = audio_cfg['parts_count']
    await get_file(audiourl, session, headers, audio_parts_count, audio_temp_filename, audio_config_filename,
                   audio_official_filename, audio_audio_size, audio_parts, audio_succeed_parts_size)


async def get_file(url, session, headers, parts_count, temp_filename, config_filename, official_filename, size,
                   parts, succeed_parts_size, multipart_chunksize=2 * 1024 * 1024):
    '''

    :param url: 请求文件所需的地址
    :param session: 请求所需的共同session
    :param headers: 请求文件所必须的请求头
    :param parts_count: 整体文件共分为多少份
    :param temp_filename: 缓存文件名
    :param config_filename: 文件配置，记录所请求的文件的基本信息
    :param official_filename: 正式文件名
    :param size: 文件具体大小
    :param parts: 本次请求的所有文件块信息
    :param succeed_parts_size: 已请求成功的文件块信息
    :param multipart_chunksize: 每次请求文件块的大小
    :return:
    '''

    sem = asyncio.Semaphore(3)
    _fetchByRange_partial = partial(_fetchByRange, sem, session, url, headers, temp_filename, config_filename)
    to_do = []  # 保存所有任务的列表
    for part_number in parts:

        if part_number != parts_count - 1:
            start = part_number * multipart_chunksize
            stop = (part_number + 1) * multipart_chunksize - 1
        else:
            start = part_number * multipart_chunksize
            stop = size - 1

        task = asyncio.ensure_future(_fetchByRange_partial(part_number, start, stop))
        to_do.append(task)

    to_do_iter = asyncio.as_completed(to_do)
    # to_do_iter = await asyncio.gather(*to_do)

    failed_parts = 0  # 下载失败的分块数目
    with tqdm(total=size, initial=succeed_parts_size, unit='B', unit_scale=True, unit_divisor=1024,
              desc=official_filename) as bar:  # 打印下载时的进度条，并动态显示下载速度
        for future in to_do_iter:
            result = await future
            # result = future
            if result.get('failed'):
                failed_parts += 1
            else:
                bar.update(result.get('part')['Size'])

    if failed_parts > 0:
        print(
            'Failed to download {}, failed parts: {}, successful parts: {}'.format(official_filename, failed_parts,
                                                                                   parts_count - failed_parts))
    else:
        # pass
        # 整个文件内容被成功下载后，将临时文件名修改回正式文件名、删除配置文件
        os.rename(temp_filename, official_filename)
        if os.path.exists(config_filename):
            os.remove(config_filename)
        print('{} downloaded'.format(official_filename))


async def get_video(videourl, session, name, headers, multipart_chunksize=2 * 1024 * 1024):
    async with session.head(videourl, headers=headers) as audio_response:
        official_filename = name + '.m4s'
        temp_filename = official_filename + '.tem'
        config_filename = official_filename + '.cfg'
        video_size = int(audio_response.headers.get('Content-Length'))
        # 获取文件的总块数
        div, mod = divmod(video_size, multipart_chunksize)
        parts_count = div if mod == 0 else div + 1  # 计算出多少个分块
        succeed_parts_size = 0
        parts = range(parts_count)
        set_parts = list(parts)
        async with aiofiles.open(temp_filename, 'wb') as fp:
            print(f'创建了{temp_filename}')

        with open(config_filename, 'w') as fp:  # 创建配置文件
            cfg = {

                'successparts': [],  # 已请求成功的文件块信息
                'parts_count': parts_count,  # 总文件块数
                'partnums': set_parts,  # 总文件块索引的集合
                'size': video_size  # 文件总大小
            }
            json.dump(cfg, fp)
        await get_file(videourl, session, headers, parts_count, temp_filename, config_filename, official_filename,
                       video_size,
                       parts, succeed_parts_size)


async def get_audio(audiourl, session, name, headers, multipart_chunksize=2 * 1024 * 1024):
    async with session.head(audiourl, headers=headers) as audio_response:
        official_filename = name + '.mp3'
        temp_filename = official_filename + '.tem'
        config_filename = official_filename + '.cfg'
        audio_size = int(audio_response.headers.get('Content-Length'))
        # 获取文件的总块数
        div, mod = divmod(audio_size, multipart_chunksize)
        parts_count = div if mod == 0 else div + 1  # 计算出多少个分块
        succeed_parts_size = 0
        parts = range(parts_count)
        set_parts = list(parts)
        async with aiofiles.open(temp_filename, 'wb') as fp:
            pass

        with open(config_filename, 'w') as fp:  # 创建配置文件
            cfg = {
                'successparts': [],  # 已请求成功的文件块信息
                'parts_count': parts_count,  # 总文件块数
                'partnums': set_parts,  # 总文件块索引的集合
                'size': audio_size  # 文件总大小
            }
            json.dump(cfg, fp)
        await get_file(audiourl, session, headers, parts_count, temp_filename, config_filename, official_filename,
                       audio_size,
                       parts, succeed_parts_size)


async def _fetchByRange(semaphore, session, url, headers, temp_filename, config_filename, part_number, start, stop):
    '''根据 HTTP headers 中的 Range 只下载一个块 (rb+ 模式)
    semaphore: 限制并发的协程数
    session: aiohttp 会话
    url: 远程目标文件的 URL 地址
    temp_filename: 临时文件
    config_filename: 配置文件
    part_number: 块编号(从 0 开始)
    start: 块的起始位置
    stop: 块的结束位置
    '''
    part_length = stop - start + 1
    range_head = {'range': 'bytes=%d-%d' % (start, stop)}
    headers.update(range_head)  # 此片段的请求头

    try:
        async with semaphore:
            async with session.get(url, headers=headers) as r:
                # 此分块的信息
                part = {
                    # 'ETag': r.headers['ETag'],
                    # 'Last-Modified': r.headers['Last-Modified'],
                    'PartNumber': part_number,
                    'Size': part_length
                }

                async with aiofiles.open(temp_filename,
                                         'rb+') as fp:  # 注意: 不能用 a 模式哦，那样的话就算用 seek(0, 0) 移动指针到文件开头后，还是会从文件末尾处追加
                    await fp.seek(start)  # 移动文件指针
                    print('[{}] File point: {}'.format(temp_filename.strip('.swp'), fp.tell()))
                    binary_content = await r.read()  # Binary Response Content: access the response body as bytes, for non-text requests
                    await fp.write(binary_content)  # 写入已下载的字节
                    print('写入成功')

                # 读取原配置文件中的内容
                f = open(config_filename, 'r')
                cfg = json.load(f)
                f.close()
                # 更新配置文件，写入此分块的信息
                f = open(config_filename, 'w')
                cfg['successparts'].append(part)
                json.dump(cfg, f)
                f.close()

                print('[{}] Part Number {} [Range: bytes={}-{}] downloaded'.format(temp_filename.strip('.swp'),
                                                                                   part_number, start, stop))
                return {
                    'part': part,
                    'failed': False  # 用于告知 _fetchByRange() 的调用方，此 Range 成功下载
                }
    except Exception as e:
        print('[{}] Part Number {} [Range: bytes={}-{}] download failed, the reason is that {}'.format(
            temp_filename.strip('.swp'), part_number, start, stop, e))
        return {
            'failed': True  # 用于告知 _fetchByRange() 的调用方，此 Range 下载失败了
        }


if __name__ == '__main__':
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:73.0) Gecko/20100101 Firefox/73.0',
    }

    file_headers = {
        'accept': '*/*',
        'accept-encoding': 'identity',
        'accept-language': 'zh-CN,zh-TW;q=0.9,zh;q=0.8,en-US;q=0.7,en;q=0.6,zh-HK;q=0.5',
        'origin': 'https://www.bilibili.com',
        'referer': 'https://www.bilibili.com/video/',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36',
    }
    url = 'https://www.bilibili.com/video/BV1Qz411v7Qg'
    loop = asyncio.get_event_loop()
    loop.run_until_complete(fast(url, headers, file_headers))