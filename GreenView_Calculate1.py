import time
import os
import numpy as np
from PIL import Image
import requests
from io import BytesIO

def VegetationClassification(img):
    """
    Classifies vegetation using the Excess Green Index (ExG).
    Returns percentage of green pixels.
    """
    try:
        img = np.asarray(img)
        if img.shape[2] == 4:  # Remove alpha channel if present
            img = img[:, :, :3]
        img = img.astype('float')
        R, G, B = img[:, :, 0], img[:, :, 1], img[:, :, 2]
        ExG = 2 * G - R - B
        binary_mask = ExG > 20  # Empirical threshold
        green_pixel_count = np.count_nonzero(binary_mask)
        total_pixels = img.shape[0] * img.shape[1]
        green_percent = (green_pixel_count / total_pixels) * 100
        return green_percent
    except Exception as e:
        print(f"[ERROR] Vegetation classification failed: {e}")
        return -1

def GreenViewComputing_ogr_6Horizon(GSVinfoFolder, outTXTRoot, greenmonth, key_file):
    # Load API keys
    with open(key_file, "r") as f:
        keylist = [line.strip() for line in f if line.strip()]
    print('API key list loaded:', keylist)

    # Define viewing angles
    headingArr = 360 / 6 * np.array([0, 1, 2, 3, 4, 5])
    numGSVImg = float(len(headingArr))
    pitch = 0

    if not os.path.exists(outTXTRoot):
        os.makedirs(outTXTRoot)

    if not os.path.isdir(GSVinfoFolder):
        print('[ERROR] GSV metadata folder not found.')
        return

    allTxtFiles = os.listdir(GSVinfoFolder)
    for txtfile in allTxtFiles:
        if not txtfile.endswith('.txt'):
            continue

        txtfilename = os.path.join(GSVinfoFolder, txtfile)
        with open(txtfilename, "r") as f:
            lines = f.readlines()

        panoIDLst = []
        panoDateLst = []
        panoLonLst = []
        panoLatLst = []

        for line in lines:
            line = line.strip()
            if not line or 'panoID' not in line:
                continue
            try:
                parts = dict(item.strip().split(": ", 1) for item in line.split(" | "))
                panoID = parts["panoID"]
                panoDate = parts["panoDate"]
                month = panoDate[-2:]
                lat = parts["lat"]
                lon = parts["lon"]
                if month in greenmonth:
                    panoIDLst.append(panoID)
                    panoDateLst.append(panoDate)
                    panoLonLst.append(lon)
                    panoLatLst.append(lat)
            except Exception as e:
                print(f"[WARN] Skipping line: {line}\nReason: {e}")
                continue

        gvTxt = 'GV_' + os.path.basename(txtfile)
        GreenViewTxtFile = os.path.join(outTXTRoot, gvTxt)
        print(f'[INFO] Processing file: {GreenViewTxtFile}')

        if os.path.exists(GreenViewTxtFile):
            print(f'[INFO] Skipping existing file: {gvTxt}')
            continue

        with open(GreenViewTxtFile, "w") as gvResTxt:
            for i in range(len(panoIDLst)):
                panoID = panoIDLst[i]
                panoDate = panoDateLst[i]
                lat = panoLatLst[i]
                lon = panoLonLst[i]
                key = keylist[i % len(keylist)]
                greenPercent = 0.0

                for heading in headingArr:
                    try:
                        URL = (
                            f"https://maps.googleapis.com/maps/api/streetview?"
                            f"size=400x400&pano={panoID}&fov=60&heading={heading}&pitch={pitch}"
                            f"&sensor=false&key={key}"
                        )
                        time.sleep(1)  # avoid rate limiting
                        response = requests.get(URL)
                        if response.status_code != 200:
                            print(f"[ERROR] Failed to fetch pano: {panoID}, status: {response.status_code}")
                            greenPercent = -1000
                            break

                        im = Image.open(BytesIO(response.content))
                        percent = VegetationClassification(im)
                        if percent == -1:
                            greenPercent = -1000
                            break
                        greenPercent += percent

                    except Exception as e:
                        print(f"[ERROR] Failed image fetch/classify: {e}")
                        greenPercent = -1000
                        break

                greenViewVal = greenPercent / numGSVImg if greenPercent >= 0 else -1
                print(f"[RESULT] Green View Index: {greenViewVal:.2f}, pano: {panoID}, ({lat}, {lon})")
                gvResTxt.write(
                    f'panoID: {panoID} panoDate: {panoDate} longitude: {lon} latitude: {lat}, greenview: {greenViewVal:.2f}\n'
                )

# ------------------------------ Main function -------------------------------
if __name__ == "__main__":
    import os

    GSVinfoRoot = r'C:\Treepedia_Public-master\spatial-data\metadata'
    outputTextPath = r'C:\Treepedia_Public-master\spatial-data\greenviewRes'
    greenmonth = ['01','02','03','04','05','06','07','08','09','10','11','12']  # or subset
    key_file = r'C:\Treepedia_Public-master\Treepedia\keys1.txt'

GreenViewComputing_ogr_6Horizon(GSVinfoRoot, outputTextPath, greenmonth, key_file)

