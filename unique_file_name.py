import os

def rename_files_uniquely_per_subfolder(main_folder_path):
    if not os.path.isdir(main_folder_path):
        print("❌ Invalid folder path.")
        return

    for root, dirs, files in os.walk(main_folder_path):
        if root == main_folder_path:
            continue  # Skip the main folder itself, only do subfolders

        subfolder_name = os.path.basename(root)
        files.sort()  # Optional for consistent ordering

        for index, filename in enumerate(files):
            old_path = os.path.join(root, filename)
            file_ext = os.path.splitext(filename)[1]  # Keep extension
            new_filename = f"{subfolder_name}_{index + 1}{file_ext}"
            new_path = os.path.join(root, new_filename)

            try:
                os.rename(old_path, new_path)
                print(f"✅ Renamed: {old_path} ➝ {new_path}")
            except Exception as e:
                print(f"❌ Error renaming {old_path}: {e}")

if __name__ == "__main__":
    folder_path = input("📂 Enter the path of the main folder: ").strip()
    rename_files_uniquely_per_subfolder(folder_path)
