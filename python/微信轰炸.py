from pynput.keyboard import Controller as a
from pynput.mouse import Button, Controller as b
import time
content = input('输入')
time.sleep(3)
for i in range(9):
    keyboard = a().type(content)
    time.sleep(1)
    mouse = b

