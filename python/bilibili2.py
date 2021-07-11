import os
import threadpool

'''
bilibili 视频批量多线程下载
'''


def download(i):
    try:
        print(i)
        os.system("you-get --format=flv720 https://www.bilibili.com/video/BV1Gf4y1q7SG?p=" + str(i))
    except:
        print('error ' + str(i))


name_list = range(23, 57)
pool = threadpool.ThreadPool(3)
requests = threadpool.makeRequests(download, name_list)
[pool.putRequest(req) for req in requests]
pool.wait()
