import os
import time
import json
import urllib.request
from osgeo import ogr, osr

def GSVpanoMetadataCollector(samplesFeatureClass, num, outputTextFolder, api_key):
    '''
    Collects metadata of Google Street View Panoramas from a shapefile of sample points.

    Parameters: 
        samplesFeatureClass (str): Path to input shapefile (.shp).
        num (int): Number of points per batch.
        outputTextFolder (str): Folder to save output .txt files.
        api_key (str): Your Google Street View API key.
    '''

    # Ensure output folder exists
    if not os.path.exists(outputTextFolder):
        os.makedirs(outputTextFolder)

    # Open shapefile
    driver = ogr.GetDriverByName('ESRI Shapefile')
    dataset = driver.Open(samplesFeatureClass)
    if dataset is None:
        print(f"❌ ERROR: Cannot open shapefile: {samplesFeatureClass}")
        return

    layer = dataset.GetLayer()
    sourceProj = layer.GetSpatialRef()
    needTransform = True

    # Determine whether transformation is needed
    targetProj = osr.SpatialReference()
    targetProj.ImportFromEPSG(4326)  # WGS84

    if sourceProj and sourceProj.IsSameGeogCS(targetProj):
        print("✅ Coordinate system is already WGS84. No transformation needed.")
        needTransform = False
    else:
        print("🔁 Coordinate system is NOT WGS84. Applying transformation.")
        transform = osr.CoordinateTransformation(sourceProj, targetProj)

    featureCount = layer.GetFeatureCount()
    batchCount = featureCount // num + (1 if featureCount % num != 0 else 0)

    print(f"📌 Total features: {featureCount} | Batch size: {num} | Batches: {batchCount}")

    for batch in range(batchCount):
        start = batch * num
        end = min((batch + 1) * num, featureCount)
        outputFile = os.path.join(outputTextFolder, f'Pnt_start{start}_end{end}.txt')

        if os.path.exists(outputFile):
            print(f"⏭️ Skipping existing batch file: {outputFile}")
            continue

        time.sleep(1)  # gentle delay between batches

        with open(outputFile, 'w', encoding='utf-8') as panoInfoText:
            print(f"🟢 Processing batch {batch + 1}/{batchCount} → {outputFile}")

            for i in range(start, end):
                feature = layer.GetFeature(i)
                geom = feature.GetGeometryRef()

                if geom is None:
                    print(f"⚠️ Feature {i} has no geometry. Skipping.")
                    continue

                if needTransform:
                    geom.Transform(transform)

                lon = geom.GetX()
                lat = geom.GetY()

                # Construct correct API URL (lat,lon format)
                url = (
                    f"https://maps.googleapis.com/maps/api/streetview/metadata"
                    f"?location={lat},{lon}&key={api_key}"
                )

                try:
                    with urllib.request.urlopen(url) as response:
                        metadata = response.read()
                    data = json.loads(metadata)
                except Exception as e:
                    print(f"❌ Error at feature {i} ({lat}, {lon}): {e}")
                    continue

                if data.get('status') != 'OK':
                    print(f"⚠️ No panorama at lat={lat}, lon={lon} → Status: {data.get('status')}")
                    panoInfoText.write(f"No panorama at lat={lat}, lon={lon} — Status: {data.get('status')}\n")
                    continue

                panoId = data.get('pano_id', 'N/A')
                panoDate = data.get('date', 'N/A')
                panoLat = data.get('location', {}).get('lat', 'N/A')
                panoLon = data.get('location', {}).get('lng', 'N/A')

                print(f"✅ Feature {i}: lat={panoLat}, lon={panoLon}, panoID={panoId}, date={panoDate}")
                line = f"panoID: {panoId} | panoDate: {panoDate} | lat: {panoLat} | lon: {panoLon}\n"
                panoInfoText.write(line)

    print("✅ Metadata collection finished for all batches.")

# ------------ MAIN -------------
if __name__ == "__main__":
    root = r'C:\Treepedia_Public-master\spatial-data'
    inputShp = os.path.join(root, 'Cambridge20m.shp')  # Ensure .shx, .dbf also exist in the same folder
    outputTxt = root
    api_key = 'AIzaSyBlsTOJ0_R9BqM7IfbU5kcgGFmBG2OY7Jc'  # 🔑 Replace with your valid API key

    GSVpanoMetadataCollector(inputShp, 1000, outputTxt, api_key)
