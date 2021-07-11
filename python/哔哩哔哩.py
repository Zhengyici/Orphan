import sys
from you_get import common as you_get

directory = r'H:\周政易\media'  # 设置下载目录
url = 'https://www.bilibili.com/bangumi/play/ep291269?from=search&seid=8835233936629819238'  # 需要下载的视频地址
sys.argv = ['you-get', '-l', '-o', directory, url]  # sys传递参数执行下载，就像在命令行一样；‘-l’是指按列表下载，如果下载单个视频，去掉‘-l’即可；‘-o’后面跟保存目录。
you_get.main()
