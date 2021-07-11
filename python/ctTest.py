import cv2

print(cv2.__version__)

cap = cv2.VideoCapture("h:/test.mp4")

idx=0
while(True):
    r, img = cap.read()
    if(r==True):
        idx += 1
        cv2.imshow("this is picture", img)
        cv2.waitKey(0)
        cv2.imwrite("h:/img-%04d.jpg"%(idx), img)

