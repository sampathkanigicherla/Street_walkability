import os

def extract_pano_ids_from_folder(folder):
    pano_data = {}
    for file in os.listdir(folder):
        if file.endswith(".txt"):
            with open(os.path.join(folder, file), 'r') as f:
                for line in f:
                    if 'panoID:' in line:
                        pano_id = line.split('panoID:')[1].split()[0]
                        pano_data[pano_id] = line.strip()
    return pano_data

def find_missing_gvi_and_images(metadata_folder, gvi_folder, image_folder_root, output_txt="missing_panoids_report.txt"):
    print("🔍 Extracting panoIDs from metadata...")
    metadata_panos = extract_pano_ids_from_folder(metadata_folder)

    print("✅ Total panoIDs in metadata:", len(metadata_panos))

    print("🔍 Extracting panoIDs from GVI...")
    gvi_panos = extract_pano_ids_from_folder(gvi_folder)
    print("✅ Total panoIDs with GVI:", len(gvi_panos))

    missing_gvi = []
    missing_images = []

    for pano_id in metadata_panos:
        # Check GVI
        if pano_id not in gvi_panos:
            missing_gvi.append(pano_id)

        # Check images
        pano_image_path = os.path.join(image_folder_root, pano_id)
        if not os.path.exists(pano_image_path) or not any(fname.lower().endswith(('.jpg', '.png')) for fname in os.listdir(pano_image_path)):
            missing_images.append(pano_id)

    # Write report
    with open(output_txt, "w") as out:
        out.write("=== Missing GVI ===\n")
        for pid in missing_gvi:
            out.write(f"{pid}\n")

        out.write("\n=== Missing Images ===\n")
        for pid in missing_images:
            out.write(f"{pid}\n")

    print("✅ Report generated:", output_txt)
    print("🧾 Missing GVI:", len(missing_gvi))
    print("🖼️ Missing Images:", len(missing_images))


# === USAGE ===
# Replace these paths with your actual folders
metadata_folder = r"C:\Treepedia_Public-master\india_city_shapefiles\Nellore\shape\metadata"
gvi_folder = r"C:\Treepedia_Public-master\india_city_shapefiles\Nellore\shape\green_view_index"
image_folder_root = r"C:\Treepedia_Public-master\india_city_shapefiles\Nellore\shape\panorama_images"

find_missing_gvi_and_images(metadata_folder, gvi_folder, image_folder_root)
