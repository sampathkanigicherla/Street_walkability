# Google Street View Panorama Metadata Collector (Python 3 Version)
# Modified for Python 3 by OpenAI Assistant
# Original by Xiaojiang Li, Senseable City Lab, MIT

import os
import time
import json
import urllib.request
from osgeo import ogr, osr

def GSVpanoMetadataCollector(samplesFeatureClass, num, outputTextFolder, api_key):
    if not os.path.exists(outputTextFolder):
        os.makedirs(outputTextFolder)

    driver = ogr.GetDriverByName('ESRI Shapefile')
    dataset = driver.Open(samplesFeatureClass)
    if dataset is None:
        print(f"❌ ERROR: Could not open shapefile: {samplesFeatureClass}")
        return

    layer = dataset.GetLayer()
    sourceProj = layer.GetSpatialRef()
    targetProj = osr.SpatialReference()
    targetProj.ImportFromEPSG(4326)

    # Only create transformation if needed
    if sourceProj.IsSame(targetProj) != 1:
        transform = osr.CoordinateTransformation(sourceProj, targetProj)
    else:
        transform = None

    featureNum = layer.GetFeatureCount()
    batch = featureNum // num + (1 if featureNum % num != 0 else 0)

    print(f"🟡 Total features: {featureNum} | Batch size: {num} | Total batches: {batch}")

    for b in range(batch):
        start = b * num
        end = min((b + 1) * num, featureNum)
        outputTextFile = f'Pnt_start{start}_end{end}.txt'
        outputGSVinfoFile = os.path.join(outputTextFolder, outputTextFile)

        if os.path.exists(outputGSVinfoFile):
            print(f"⏭️ Skipping existing file: {outputTextFile}")
            continue

        time.sleep(1)

        with open(outputGSVinfoFile, 'w', encoding='utf-8') as panoInfoText:
            print(f"🟢 Processing batch {b + 1}/{batch} → saving to {outputTextFile}")

            for i in range(start, end):
                feature = layer.GetFeature(i)
                geom = feature.GetGeometryRef()

                if geom is None:
                    print(f"⚠️ No geometry for feature {i}, skipping.")
                    continue

                # Clone and transform if needed
                geom = geom.Clone()
                if transform:
                    geom.Transform(transform)

                lon = geom.GetX()
                lat = geom.GetY()

                print(f"🔍 Testing point {i}: lat={lat}, lon={lon}")

                url = (
                    f"https://maps.googleapis.com/maps/api/streetview/metadata"
                    f"?location={lat},{lon}&key={api_key}"
                )

                try:
                    with urllib.request.urlopen(url) as response:
                        metaData = response.read()
                    data = json.loads(metaData)
                except Exception as e:
                    print(f"❌ Error retrieving data for point {i}: {e}")
                    continue

                if data.get('status') != 'OK':
                    print(f"⚠️ Point {i} — No panorama found. Status: {data.get('status')}")
                    continue

                panoId = data.get('pano_id', 'N/A')
                panoDate = data.get('date', 'N/A')
                panoLat = data.get('location', {}).get('lat', 'N/A')
                panoLon = data.get('location', {}).get('lng', 'N/A')

                print(f"✅ Point {i}: ({panoLon},{panoLat}), panoId: {panoId}, panoDate: {panoDate}")
                lineTxt = f'panoID: {panoId} panoDate: {panoDate} longitude: {panoLon} latitude: {panoLat}\n'
                panoInfoText.write(lineTxt)

    print("✅ All batches complete. Metadata saved to output folder.")


# ------------Main Function -------------------
if __name__ == "__main__":
    root = r'C:\Treepedia_Public-master\spatial-data'
    inputShp = os.path.join(root, 'Cambridge20m.shp')
    outputTxt = root

    # 🔑 Replace with your actual API key
    api_key = 'AIzaSyBlsTOJ0_R9BqM7IfbU5kcgGFmBG2OY7Jc'

    GSVpanoMetadataCollector(inputShp, 1000, outputTxt, api_key)
