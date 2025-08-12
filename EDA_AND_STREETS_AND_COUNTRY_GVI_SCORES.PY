import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def load_gvi_data(gvi_folder):
    all_data = []

    for file in os.listdir(gvi_folder):
        if file.startswith("GV_") and file.endswith(".txt"):
            path = os.path.join(gvi_folder, file)
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    if 'greenview:' not in line:
                        continue
                    try:
                        parts = dict(item.strip().split(": ", 1) for item in line.strip().split("  ") if ": " in item)
                        all_data.append({
                            "panoID": parts.get("panoID", ""),
                            "street_id": parts.get("street_id", "NA"),
                            "street_name": parts.get("street_name", "NA"),
                            "point_id": int(parts.get("point_id", -1)),
                            "greenview": float(parts.get("greenview", -1)),
                        })
                    except Exception as e:
                        print(f"⚠️ Skipping line due to parse error: {e}\n{line}")
                        continue

    return pd.DataFrame(all_data)

def compute_streetwise_gvi(df):
    street_gvi = df.groupby("street_id")["greenview"].mean().reset_index()
    street_gvi.columns = ["street_id", "avg_gvi"]
    return street_gvi

def save_eda(df, street_gvi, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    # Histogram
    plt.figure(figsize=(10, 6))
    sns.histplot(street_gvi["avg_gvi"], bins=30, kde=True)
    plt.title("Distribution of Street GVI")
    plt.xlabel("Average GVI")
    plt.ylabel("Street Count")
    plt.savefig(os.path.join(output_folder, "gvi_histogram.png"))
    plt.close()

    # Boxplot
    plt.figure(figsize=(8, 5))
    sns.boxplot(y=street_gvi["avg_gvi"])
    plt.title("Boxplot of Street GVI")
    plt.ylabel("Average GVI")
    plt.savefig(os.path.join(output_folder, "gvi_boxplot.png"))
    plt.close()

    # Top and Bottom Streets
    top10 = street_gvi.sort_values(by="avg_gvi", ascending=False).head(10)
    bottom10 = street_gvi.sort_values(by="avg_gvi", ascending=True).head(10)

    top10.to_csv(os.path.join(output_folder, "top_10_greenest_streets.csv"), index=False)
    bottom10.to_csv(os.path.join(output_folder, "least_10_green_streets.csv"), index=False)

def main():
    gvi_folder = r"C:\Treepedia_Public-master\india_city_shapefiles\Nellore\shape\green_view_index"
    output_folder = r"C:\Treepedia_Public-master\india_city_shapefiles\Nellore\shape"

    print("📥 Reading GVI data...")
    df = load_gvi_data(gvi_folder)
    if df.empty:
        print("❌ No valid GVI data found.")
        return

    print("📊 Computing per-street GVI...")
    street_gvi = compute_streetwise_gvi(df)
    street_gvi.to_csv(os.path.join(output_folder, "street_avg_gvi.csv"), index=False)

    print("🌏 Calculating overall average GVI...")
    overall_gvi = df["greenview"].mean()
    with open(os.path.join(output_folder, "overall_gvi.txt"), "w") as f:
        f.write(f"Overall GVI: {overall_gvi:.2f}\n")

    print("📈 Generating EDA plots and top/bottom street analysis...")
    save_eda(df, street_gvi, output_folder)

    print(f"\n✅ Done! Results saved in: {output_folder}")

if __name__ == "__main__":
    main()
