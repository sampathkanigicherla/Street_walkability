import os
import time
import json
import urllib.request
from osgeo import ogr, osr

def GSVpanoMetadataCollector(samplesFeatureClass, num, outputTextFolder, key_file):
    """
    Collects metadata of Google Street View Panoramas from sample points shapefile.
    Rotates through multiple API keys from a .txt file.
    """

    # ✅ Load all API keys
    with open(key_file, "r") as f:
        keylist = [line.strip() for line in f if line.strip()]
    if not keylist:
        print("❌ No valid API keys found.")
        return
    print(f"✅ Loaded {len(keylist)} API keys.")

    if not os.path.exists(outputTextFolder):
        os.makedirs(outputTextFolder)

    driver = ogr.GetDriverByName('ESRI Shapefile')
    dataset = driver.Open(samplesFeatureClass)
    if dataset is None:
        print(f"❌ Cannot open shapefile: {samplesFeatureClass}")
        return

    layer = dataset.GetLayer()
    sourceProj = layer.GetSpatialRef()

    # 🔁 Check projection, reproject if not WGS84
    needTransform = True
    targetProj = osr.SpatialReference()
    targetProj.ImportFromEPSG(4326)
    if sourceProj and sourceProj.IsSameGeogCS(targetProj):
        needTransform = False
        print("✅ Projection is WGS84. No transform needed.")
    else:
        transform = osr.CoordinateTransformation(sourceProj, targetProj)
        print("🔁 Transforming coordinates to WGS84.")

    featureCount = layer.GetFeatureCount()
    totalBatches = featureCount // num + (1 if featureCount % num != 0 else 0)
    print(f"📍 Total points: {featureCount} | Batch size: {num} | Total batches: {totalBatches}")

    for batch in range(totalBatches):
        start = batch * num
        end = min((batch + 1) * num, featureCount)
        outputFile = os.path.join(outputTextFolder, f'Pnt_start{start}_end{end}.txt')

        if os.path.exists(outputFile):
            print(f"⏭️ Skipping existing: {outputFile}")
            continue

        print(f"🟢 Processing batch {batch + 1}/{totalBatches} → {outputFile}")
        time.sleep(1)

        with open(outputFile, 'w', encoding='utf-8') as panoInfoText:
            for i in range(start, end):
                feature = layer.GetFeature(i)
                geom = feature.GetGeometryRef()
                if geom is None:
                    print(f"⚠️ Feature {i} has no geometry. Skipping.")
                    continue

                if needTransform:
                    geom.Transform(transform)

                lat, lon = geom.GetY(), geom.GetX()

                # 🏷️ Extract attributes (if missing, fallback to 'NA')
                street_id = feature.GetField('street_id') or 'NA'
                street_name = feature.GetField('street_nam') or 'NA'
                point_id = feature.GetField('point_id') or feature.GetFID()

                # 🔐 Use rotating API keys
                key = keylist[i % len(keylist)]
                url = (
                    f"https://maps.googleapis.com/maps/api/streetview/metadata"
                    f"?location={lat},{lon}&key={key}"
                )

                try:
                    with urllib.request.urlopen(url) as response:
                        metadata = response.read()
                    data = json.loads(metadata)
                except Exception as e:
                    print(f"❌ Error: {e} | feature {i} | ({lat}, {lon})")
                    continue

                status = data.get('status')
                if status != 'OK':
                    print(f"⚠️ No panorama at ({lat}, {lon}) → Status: {status}")
                    continue

                panoId = data.get('pano_id', 'N/A')
                panoDate = data.get('date', 'N/A')
                panoLat = data.get('location', {}).get('lat', lat)
                panoLon = data.get('location', {}).get('lng', lon)

                print(f"✅ panoID: {panoId} | lat: {panoLat} | lon: {panoLon}")

                # ✍️ Write line with full metadata
                line = (
                    f"panoID: {panoId}  panoDate: {panoDate}  lat: {panoLat}  lon: {panoLon}  "
                    f"street_id: {street_id}  street_name: {street_name}  point_id: {point_id}\n"
                )
                panoInfoText.write(line)

    print("✅ Metadata collection complete.")

# ---------------- MAIN ----------------
if __name__ == "__main__":
    inputShp = r'C:\Treepedia_Public-master\india_city_shapefiles\Nellore\create_points\create_points.shp'
    outputTxt = r'C:\Treepedia_Public-master\india_city_shapefiles\Nellore\metadata'
    key_file = r'C:\Treepedia_Public-master\Treepedia\keys1.txt'
    GSVpanoMetadataCollector(inputShp, 1000, outputTxt, key_file)
