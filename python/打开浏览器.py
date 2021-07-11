from selenium import webdriver
import os


a = input("百度：")
b = ("https://www.baidu.com/s?wd=")
c = b + a
wd = webdriver.Chrome()
print(c)
wd.get(c)

