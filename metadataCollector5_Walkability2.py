import os
import time
import json
import urllib.request
from osgeo import ogr, osr

def safe_get_field(feature, field_name):
    """Returns the field value if it exists, else 'None'."""
    try:
        return feature.GetField(field_name)
    except:
        return "None"

def GSVpanoMetadataCollector(samplesFeatureClass, num, outputTextFolder, key_file):
    """
    Collects metadata of Google Street View Panoramas from sample points shapefile.
    Rotates through multiple API keys from a .txt file.
    """

    # ✅ Load all API keys
    with open(key_file, "r") as f:
        keylist = [line.strip() for line in f if line.strip()]
    if not keylist:
        print("❌ No API keys found.")
        return
    print(f"✅ Loaded {len(keylist)} API keys.")

    # ✅ Set driver and open shapefile
    driver = ogr.GetDriverByName('ESRI Shapefile')
    dataSource = driver.Open(samplesFeatureClass, 0)
    if not dataSource:
        print("❌ Could not open the shapefile.")
        return

    layer = dataSource.GetLayer()

    # ✅ Show all available field names for debugging
    print("📋 Available fields in shapefile:")
    layer_defn = layer.GetLayerDefn()
    for i in range(layer_defn.GetFieldCount()):
        print("-", layer_defn.GetFieldDefn(i).GetName())

    # ✅ Check projection
    spatialRef = layer.GetSpatialRef()
    wgs84 = osr.SpatialReference()
    wgs84.ImportFromEPSG(4326)

    if spatialRef.IsSame(wgs84):
        transform_needed = False
        print("✅ Projection is WGS84. No transformation needed.")
    else:
        transform_needed = True
        transform = osr.CoordinateTransformation(spatialRef, wgs84)
        print("🔁 Coordinate transformation will be applied.")

    # ✅ Batch processing
    batch_size = 1000
    total_features = layer.GetFeatureCount()
    total_batches = (total_features // batch_size) + 1
    print(f"📍 Total points: {total_features} | Batch size: {batch_size} | Total batches: {total_batches}")

    # ✅ Resume logic
    log_path = os.path.join(outputTextFolder, "resume_status.log")
    resume_index = 0
    resume_file = None
    if os.path.exists(log_path):
        with open(log_path, "r") as f:
            line = f.read().strip()
            if line:
                resume_file, resume_index = line.split(",")
                resume_index = int(resume_index)
                print(f"🔁 Resuming from: {resume_file} after {resume_index} panoIDs")

    # ✅ Loop through batches
    for batch_idx in range(total_batches):
        start = batch_idx * batch_size
        end = min((batch_idx + 1) * batch_size, total_features)
        filename = f"Pnt_start{start}_end{end}.txt"
        output_path = os.path.join(outputTextFolder, filename)

        if resume_file and filename < resume_file:
            print(f"⏭️ Skipping completed file: {filename}")
            continue

        # ✅ Open file for writing/appending
        panoInfoText = open(output_path, "a+", encoding='utf-8')
        panoInfoText.seek(0, os.SEEK_END)
        written_count = 0

        for i in range(start, end):
            if resume_file == filename and i < resume_index:
                continue

            feature = layer.GetFeature(i)
            if not feature:
                continue
            geom = feature.GetGeometryRef()
            if transform_needed:
                geom.Transform(transform)
            lon = geom.GetX()
            lat = geom.GetY()

            # Use safe field retrieval
            point_id = safe_get_field(feature, "id")
            street_id = safe_get_field(feature, "osm_id")
            street_name = safe_get_field(feature, "name")

            key = keylist[i % len(keylist)]
            url = f"https://maps.googleapis.com/maps/api/streetview/metadata?location={lat},{lon}&key={key}"

            try:
                with urllib.request.urlopen(url) as response:
                    result = json.loads(response.read().decode())

                if result.get("status") == "OK":
                    panoID = result.get("pano_id")
                    panoDate = result.get("date", "None")
                    street_name_str = street_name if street_name else "None"

                    line = f"panoID: {panoID}  panoDate: {panoDate}  lat: {lat}  lon: {lon}  street_id: {street_id}  street_name: {street_name_str}  point_id: {point_id}\n"

                    try:
                        panoInfoText.write(line)
                        panoInfoText.flush()
                        os.fsync(panoInfoText.fileno())
                        written_count += 1
                        print(f"✅ {point_id}: panoID {panoID}, lat {lat}, lon {lon}")
                        print(f"📄 Written to file: {line.strip()}")
                    except Exception as write_err:
                        print(f"❌ Failed to write line at point_id {point_id}: {write_err}")
                        continue
                else:
                    print(f"⚠️ No GSV data at point_id {point_id}: {result.get('status')}")

                time.sleep(0.1)

            except Exception as e:
                print(f"❌ API Error at point_id {point_id}: {e}")
                time.sleep(1)
                continue

        panoInfoText.flush()
        os.fsync(panoInfoText.fileno())
        panoInfoText.close()

        # ✅ Log resume info
        with open(log_path, "w") as f:
            f.write(f"{filename},{end - 1}")
        print(f"✅ Finished file: {filename} and saved {written_count} panoIDs.\n")


# ✅ Example usage (edit paths as needed)
if __name__ == "__main__":
    shapefile_path = r"C:\Treepedia_Public-master\india_city_shapefiles\Nellore\create_points\create_points.shp"
    output_folder = r"C:\Treepedia_Public-master\india_city_shapefiles\Nellore\metadata"
    key_file_path = r"C:\Treepedia_Public-master\Treepedia\keys1.txt"
    GSVpanoMetadataCollector(shapefile_path, num=116932, outputTextFolder=output_folder, key_file=key_file_path)
