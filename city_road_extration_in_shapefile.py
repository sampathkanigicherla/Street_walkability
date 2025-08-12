import os
import osmnx as ox

def extract_city_roads(city_name, output_base_folder):
    """
    Downloads all driveable roads for a given city and saves them as a shapefile.
    """
    print(f"\n🔄 Processing: {city_name}...")
    city_folder_name = city_name.split(",")[0].replace(" ", "_").lower()
    output_folder = os.path.join(output_base_folder, city_folder_name)
    os.makedirs(output_folder, exist_ok=True)

    try:
        # Download driveable road network
        G = ox.graph_from_place(city_name, network_type='drive')

        # Convert to GeoDataFrame (edges only)
        edges = ox.graph_to_gdfs(G, nodes=False, edges=True)

        # Save roads to shapefile
        shp_path = os.path.join(output_folder, f"{city_folder_name}_roads.shp")
        edges.to_file(shp_path)

        print(f"✅ Roads saved: {shp_path}")
    except Exception as e:
        print(f"❌ Failed to process {city_name}: {e}")

# ---------------- MAIN ----------------

if __name__ == "__main__":
    # List of Indian cities
    cities = [
        "Hyderabad, India",
        "Vijayawada, India",
        "Visakhapatnam, India",
        "puna, India",
        "Bengaluru, India",
        "kochi, India",
    ]

    # Base output folder
    output_base = "C:\Treepedia_Public-master\city_road_extration_in_shapefile\city_data"

    # Extract roads for each city
    for city in cities:
        extract_city_roads(city, output_base)