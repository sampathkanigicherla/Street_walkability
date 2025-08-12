import time
import os
import numpy as np
from PIL import Image
import requests
from io import BytesIO
import torch

# Load YOLOv5 model (custom or pre-trained)
model = torch.hub.load('ultralytics/yolov5', 'custom', path='yolov5_custom.pt')  # Replace with your model path
model.conf = 0.25  # confidence threshold

def VegetationClassification(img):
    try:
        img = np.asarray(img)
        if img.shape[2] == 4:
            img = img[:, :, :3]
        img = img.astype('float')
        R, G, B = img[:, :, 0], img[:, :, 1], img[:, :, 2]
        ExG = 2 * G - R - B
        binary_mask = ExG > 20
        green_pixel_count = np.count_nonzero(binary_mask)
        total_pixels = img.shape[0] * img.shape[1]
        green_percent = (green_pixel_count / total_pixels) * 100
        return green_percent
    except Exception as e:
        print(f"[ERROR] Vegetation classification failed: {e}")
        return -1

def detect_objects_yolo(image):
    results = model(image)
    detections = results.pandas().xyxy[0]
    if not detections.empty:
        print(f"[YOLO] Detected: {detections[['name', 'confidence']].values.tolist()}")
    return detections

def GreenViewWithYOLO(GSVinfoFolder, greenmonth, key_file):
    with open(key_file, "r") as f:
        keylist = [line.strip() for line in f if line.strip()]
    headingArr = 360 / 6 * np.array([0, 1, 2, 3, 4, 5])
    pitch = 0

    if not os.path.isdir(GSVinfoFolder):
        print('[ERROR] GSV metadata folder not found.')
        return

    allTxtFiles = [f for f in os.listdir(GSVinfoFolder) if f.endswith('.txt')]
    allTxtFiles.sort()

    for batch_index, txtfile in enumerate(allTxtFiles, start=1):
        txtfilename = os.path.join(GSVinfoFolder, txtfile)
        with open(txtfilename, "r") as f:
            lines = f.readlines()

        panoIDLst, panoDateLst, panoLonLst, panoLatLst = [], [], [], []

        for line in lines:
            line = line.strip()
            if not line or 'panoID' not in line:
                continue
            try:
                parts = dict(item.strip().split(": ", 1) for item in line.split(" | "))
                panoID = parts["panoID"]
                panoDate = parts["panoDate"]
                month = panoDate[-2:]
                lat, lon = parts["lat"], parts["lon"]
                if month in greenmonth:
                    panoIDLst.append(panoID)
                    panoDateLst.append(panoDate)
                    panoLonLst.append(lon)
                    panoLatLst.append(lat)
            except Exception as e:
                print(f"[WARN] Skipping line: {line}\nReason: {e}")
                continue

        print(f"[INFO] Processing batch: {txtfile} with {len(panoIDLst)} panos")

        for i in range(len(panoIDLst)):
            panoID = panoIDLst[i]
            panoDate = panoDateLst[i]
            lat = panoLatLst[i]
            lon = panoLonLst[i]
            key = keylist[i % len(keylist)]
            greenPercent = 0.0

            print(f"[INFO] Pano: {panoID}, Date: {panoDate}, LatLon: ({lat}, {lon})")

            for heading in headingArr:
                try:
                    URL = (
                        f"https://maps.googleapis.com/maps/api/streetview?"
                        f"size=400x400&pano={panoID}&fov=60&heading={heading}&pitch={pitch}"
                        f"&key={key}"
                    )
                    time.sleep(1)
                    response = requests.get(URL)
                    if response.status_code != 200:
                        print(f"[ERROR] Failed to fetch pano: {panoID}, status: {response.status_code}")
                        greenPercent = -1000
                        break

                    im = Image.open(BytesIO(response.content)).convert("RGB")
                    percent = VegetationClassification(im)
                    if percent == -1:
                        greenPercent = -1000
                        break
                    greenPercent += percent

                    # YOLO Object Detection
                    detect_objects_yolo(im)

                except Exception as e:
                    print(f"[ERROR] Failed image fetch/classify: {e}")
                    greenPercent = -1000
                    break

            greenViewVal = greenPercent / len(headingArr) if greenPercent >= 0 else -1
            print(f"[RESULT] GVI: {greenViewVal:.2f} for panoID: {panoID}")

# ------------------------------ Main function -------------------------------
if __name__ == "__main__":
    GSVinfoRoot = r'C:\Treepedia_Public-master\spatial-data\metadata'
    greenmonth = ['01','02','03','04','05','06','07','08','09','10','11','12']
    key_file = r'C:\Treepedia_Public-master\Treepedia\keys1.txt'

    GreenViewWithYOLO(GSVinfoRoot, greenmonth, key_file)
