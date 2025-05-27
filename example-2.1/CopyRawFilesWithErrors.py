import MyGPTAPI
import os
import shutil

# used to copy the files together to check the erroneous files more easily

APICONFIG = MyGPTAPI.APIConfig()
APICONFIG.from_file("api_config.json")
KB_NAME = "KB Name"
UPLOAD_FOLDER = "some/folder"
OUTPUT_FOLDER = "some/other/folder"


def main():
    api = MyGPTAPI.MyGPTAPI(api_config=APICONFIG)
    kb_id = api.get_kb_id_by_name(KB_NAME)
    if kb_id is None:
        print("KB not found")
        exit(-1)

    not_found_local_files = 0
    copied_files = 0
    for error_file in api.get_all_kb_documents_not_in_success(kb_id):
        if error_file["status"] != "failed":
            continue

        rel_path, file_name = os.path.split(error_file['original_path'])
        org_path = os.path.join(UPLOAD_FOLDER, rel_path, file_name)
        if os.path.exists(org_path):
            folder_name = error_file["status_message"][:25].strip()
            for excl_char in "<>:\"/\\|?":
                folder_name = folder_name.replace(excl_char, "")
            if len(folder_name) == 0:
                folder_name = "NO ERROR MESSAGE"
            folder_path = os.path.join(OUTPUT_FOLDER, folder_name)
            if not os.path.exists(folder_path):
                os.mkdir(folder_path)
            with open(os.path.join(folder_path, "errors.txt"), mode="a", newline="\n", encoding="utf-8") as txt_file:
                txt_file.write(f"{file_name} {error_file["status_message"]}\n")
            shutil.copyfile(org_path, os.path.join(folder_path, file_name))
            copied_files += 1
        else:
            not_found_local_files += 1
            print(f"file not found {error_file["original_path"]}")

    print(f"copied {copied_files} erroneous files to {OUTPUT_FOLDER}")
    if not_found_local_files > 0:
        print(f"{not_found_local_files} file not found locally")


if __name__ == "__main__":
    main()
