import os
import pandas as pd

def compare_gvi_and_metadata(metadata_folder, greenview_folder, report_csv="comparison_report.csv"):
    # Detect all metadata and greenview .txt files
    metadata_files = {f for f in os.listdir(metadata_folder) if f.startswith("Pnt_") and f.endswith(".txt")}
    greenview_files = {f for f in os.listdir(greenview_folder) if f.startswith("GV_Pnt_") and f.endswith(".txt")}

    # Extract base names like: Pnt_start0_end1000.txt
    metadata_base = {f: f for f in metadata_files}
    greenview_base = {f.replace("GV_", ""): f for f in greenview_files}

    # Union of all base file names
    all_base_files = sorted(set(metadata_base.keys()).union(greenview_base.keys()))

    report_data = []
    total_missing_rows = 0

    for base_file in all_base_files:
        meta_path = os.path.join(metadata_folder, base_file)
        gv_file = greenview_base.get(base_file)
        gv_path = os.path.join(greenview_folder, gv_file) if gv_file else None

        meta_exists = os.path.exists(meta_path)
        gv_exists = os.path.exists(gv_path) if gv_file else False

        row = {"File": base_file}

        if not meta_exists and not gv_exists:
            row.update({
                "Metadata Count": "Missing",
                "GreenViewIndex Count": "Missing",
                "Status": "Both files missing",
                "Difference": "-"
            })
        elif not meta_exists:
            row.update({
                "Metadata Count": "Missing",
                "GreenViewIndex Count": "Exists",
                "Status": "Metadata file missing",
                "Difference": "-"
            })
        elif not gv_exists:
            row.update({
                "Metadata Count": "Exists",
                "GreenViewIndex Count": "Missing",
                "Status": "GreenViewIndex file missing",
                "Difference": "-"
            })
        else:
            try:
                meta_count = len(pd.read_csv(meta_path, sep=",", engine="python"))
                gv_count = len(pd.read_csv(gv_path, sep=",", engine="python"))

                row["Metadata Count"] = meta_count
                row["GreenViewIndex Count"] = gv_count

                if meta_count > gv_count:
                    status = "GreenViewIndex lacking"
                    diff = meta_count - gv_count
                elif gv_count > meta_count:
                    status = "Metadata lacking"
                    diff = gv_count - meta_count
                else:
                    status = "Equal"
                    diff = 0

                row["Status"] = status
                row["Difference"] = diff
                total_missing_rows += diff

            except Exception as e:
                row.update({
                    "Metadata Count": "Error",
                    "GreenViewIndex Count": "Error",
                    "Status": f"Error: {str(e)}",
                    "Difference": "-"
                })

        report_data.append(row)

    # Save report
    df_report = pd.DataFrame(report_data)
    df_report.to_csv(report_csv, index=False, encoding="utf-8")

    print(f"\n✅ Report generated with {len(df_report)} entries")
    print(f"📊 Total missing rows across mismatches: {total_missing_rows}")
    print(f"📁 Report saved to: {report_csv}")

# ✅ Use your .txt file folders
metadata_folder = r"C:\Treepedia_Public-master\india_city_shapefiles\Nellore\shape\metadata"
greenview_folder = r"C:\Treepedia_Public-master\india_city_shapefiles\Nellore\shape\green_view_index"
report_csv = r"C:\Treepedia_Public-master\india_city_shapefiles\Nellore\shape\comparison_report.csv"

compare_gvi_and_metadata(metadata_folder, greenview_folder, report_csv)
