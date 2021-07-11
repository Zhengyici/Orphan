import requests
from lxml import etree

url = "http://www.kachayv.cn/"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'}

# c = input("输入")
data = {"word": "你好", "fonts": "15.ttf"}

a = requests.post(url=url, headers=headers, data=data).text
html = etree.HTML(a)
img = html.xpath('//div[@class="sctp"]/img/@src')[0]
img_url = url + img
print(img_url)
b = requests.get(img_url).content
with open('img.jpg', 'wb')as f:
    f.write(b)
# print(c)
