import requests
import json

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'}
itlst = []
itcnt = []
for i in range(0, 5):
    url = 'https://club.jd.com/comment/productPageComments.action?callback=fetchJSON_comment98&productId=10021041789537&score=0&sortType=5&page=%d&pageSize=10&isShadowSku=0&fold=1' % (
        i)
    print("page:%d, url=%s\n" % (i, url))
    resp = requests.get(url, headers=headers)
    content = resp.text
    rest = content.replace('fetchJSON_comment98(', '').replace(');', '')
    data = json.loads(rest)
    comments = data['comments']

    ln = 0
    for item in comments:
        color = item['productColor']
        size = item['productSize']
        arr = "%s:%s" % (color, size)
        itIdx = 0
        has = False
        for it2 in itlst:
            print("arr:%s, it2:%s" % (arr, it2))
            if arr == it2:
                itcnt[itIdx] += 1
                has = True
            itIdx += 1

        if not has:
            itlst.append(arr)
            itcnt.append(0)

        print("page=%d, line=%d, color=%s, size=%s" % (i, ln, color, size))
        ln += 1

print("summ countOK, show the count info:")
outFileName = "/Users/funxu/fDat/yiCnt.txt"
outStr = ""
itIdx = 0
with open(outFileName, 'a+') as f:
    for it3 in itlst:
        outStr = "idx:%d, color:size(%s),  count:%d" % (itIdx, it3, itcnt[itIdx])
        print(outStr)
        f.write(outStr + "\r\n")

        itIdx += 1