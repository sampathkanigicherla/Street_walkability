import os
import time
import json
import urllib.request
from osgeo import ogr, osr

def extract_start_index(fname):
    try:
        return int(fname.split('Pnt_start')[1].split('_')[0])
    except:
        return -1

def GSVpanoMetadataCollector(samplesFeatureClass, num, outputTextFolder, key_file):
    # ✅ Load API keys
    with open(key_file, "r") as f:
        keylist = [line.strip() for line in f if line.strip()]
    if not keylist:
        print("❌ No valid API keys found.")
        return
    print(f"✅ Loaded {len(keylist)} API keys.")

    if not os.path.exists(outputTextFolder):
        os.makedirs(outputTextFolder)

    # ✅ Load Shapefile
    driver = ogr.GetDriverByName('ESRI Shapefile')
    dataset = driver.Open(samplesFeatureClass)
    if dataset is None:
        print(f"❌ Cannot open shapefile: {samplesFeatureClass}")
        return
    layer = dataset.GetLayer()
    sourceProj = layer.GetSpatialRef()

    # ✅ Projection check
    targetProj = osr.SpatialReference()
    targetProj.ImportFromEPSG(4326)
    needTransform = not (sourceProj and sourceProj.IsSameGeogCS(targetProj))
    if needTransform:
        transform = osr.CoordinateTransformation(sourceProj, targetProj)
        print("🔁 Transforming coordinates to WGS84.")
    else:
        print("✅ Projection is WGS84. No transformation needed.")

    featureCount = layer.GetFeatureCount()
    totalBatches = (featureCount // num) + (1 if featureCount % num else 0)
    print(f"📍 Total points: {featureCount} | Batch size: {num} | Total batches: {totalBatches}")

    # ✅ Resume log setup
    log_path = os.path.join(outputTextFolder, "resume_log.txt")
    resume_file = None
    resume_index = 0
    serial_start = 0

    if os.path.exists(log_path):
        with open(log_path, "r") as logf:
            line = logf.read().strip()
            if line:
                parts = line.split(",")
                if len(parts) >= 2:
                    resume_file = parts[0]
                    resume_index = int(parts[1])
                    serial_start = int(parts[2]) if len(parts) == 3 else 0
                    print(f"🔁 Resuming from: {resume_file}, index: {resume_index}, serial: {serial_start}")

    resume_start = extract_start_index(resume_file) if resume_file else -1

    for batch in range(totalBatches):
        start = batch * num
        end = min((batch + 1) * num, featureCount)
        filename = f'Pnt_start{start}_end{end}.txt'
        file_start = extract_start_index(filename)

        if resume_file and file_start < resume_start:
            print(f"⏭️ Skipping completed file: {filename}")
            continue

        # ✅ Reset or resume serial
        if filename == resume_file:
            mode = 'a'
            serial = serial_start
        else:
            mode = 'w'
            serial = 0

        print(f"\n🟢 Processing file: {filename} | Mode: {mode.upper()}")
        output_path = os.path.join(outputTextFolder, filename)

        with open(output_path, mode, encoding='utf-8') as panoInfoText:
            for i in range(start, end):
                if filename == resume_file and i < resume_index:
                    continue

                feature = layer.GetFeature(i)
                geom = feature.GetGeometryRef()
                if not geom:
                    continue

                if needTransform:
                    geom.Transform(transform)

                lat, lon = geom.GetY(), geom.GetX()

                # ✅ Extract fields safely
                street_id = feature.GetField('street_id') or 'None'
                street_name = feature.GetField('street_nam') or 'None'
                point_id = feature.GetField('point_id')
                if point_id is None:
                    point_id = i  # fallback to loop index

                key = keylist[i % len(keylist)]
                url = f"https://maps.googleapis.com/maps/api/streetview/metadata?location={lat},{lon}&key={key}"

                try:
                    with urllib.request.urlopen(url) as response:
                        data = json.loads(response.read().decode())
                except Exception as e:
                    print(f"❌ API error at index: {i} → {e}")
                    continue

                if data.get("status") != "OK":
                    continue

                panoId = data.get("pano_id", "N/A")
                panoDate = data.get("date", "N/A")
                panoLat = data.get("location", {}).get("lat", lat)
                panoLon = data.get("location", {}).get("lng", lon)

                # ✅ Compose and write output line
                line = (
                    f"panoID: {panoId}  panoDate: {panoDate}  lat: {panoLat}  lon: {panoLon}  "
                    f"street_id: {street_id}  street_name: {street_name}  point_id: {point_id}\n"
                )
                panoInfoText.write(line)
                print(f"{line.strip()}")

                # ✅ Update resume log
                with open(log_path, "w") as f:
                    f.write(f"{filename},{i},{serial}")

                serial += 1
                time.sleep(0.1)  # avoid rate limit

    print("\n✅ Metadata collection complete.")

# ---------------- MAIN ----------------
if __name__ == "__main__":
    inputShp = r'C:\Treepedia_Public-master\india_city_shapefiles\Nellore\create_points\createpoints.shp'
    outputTxt = r'C:\Treepedia_Public-master\india_city_shapefiles\Nellore\metadata'
    key_file = r'C:\Treepedia_Public-master\Treepedia\keys2.txt'
    GSVpanoMetadataCollector(inputShp, 1000, outputTxt, key_file)
