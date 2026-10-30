import cv2

backends = [
    ("DEFAULT", cv2.CAP_ANY),
    ("MSMF", cv2.CAP_MSMF),
    ("DSHOW", cv2.CAP_DSHOW),
]

for backend_name, backend in backends:
    print(f"\n===== Testing {backend_name} =====")

    for index in range(5):
        cap = cv2.VideoCapture(index, backend)

        if cap.isOpened():
            ret, frame = cap.read()

            if ret:
                print(f"✅ Camera {index} works with {backend_name}")
                cv2.imshow(f"{backend_name} - Camera {index}", frame)
                cv2.waitKey(2000)
                cv2.destroyAllWindows()

        cap.release()