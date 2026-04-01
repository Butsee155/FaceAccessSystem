import cv2

for i in range(3):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        ret, frame = cap.read()
        print(f"Index {i}: {'WORKS' if ret else 'Opens but no frame'}")
        cap.release()
    else:
        print(f"Index {i}: NOT available")