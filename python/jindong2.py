import requests
import json

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'}

for i in range(0, 5):
    url = 'https://club.jd.com/comment/productPageComments.action?callback=fetchJSON_comment98&productId=10021041789537&score=0&sortType=5&page=%d&pageSize=10&isShadowSku=0&fold=1' % (
        i)
    print("page:%d, url=%s\n" % (i, url))
    resp = requests.get(url, headers=headers)
    content = resp.text
    rest = content.replace('fetchJSON_comment98(', '').replace(');', '')
    data = json.loads(rest)
    comments = data['comments']
    for item in comments:
        color = item['productColor']
        size = item['productSize']
        print(color)
        print(size)
        with open('list.txt', 'a') as f:
            f.write(color)
        # list=[color]
    # print(list.count('白黑'))
