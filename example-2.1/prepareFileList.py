import os
from typing import List
import mimetypes
import zipfile

from UploadFiles import UploadFile, UploadFiles

BASE_PATH = "somewhere/here"
ALLOWED_FILETYPES = [".pdf", ".docx", ".txt", ".pptx", ".xlsx", ".xls", ".doc"]
IGNORE_PATTERNS = ["~$"]
FILENAME = "update_files.json"

def walk_directory(path: str, base_path: str) -> List[UploadFile]:
    upload_files: List[UploadFile] = []
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        common_prefix = os.path.commonprefix([path, base_path])
        if os.path.isdir(file_path):
            upload_files.extend(walk_directory(path=file_path, base_path=base_path))
        else:
            pattern_ok = True
            for pattern in IGNORE_PATTERNS:
                if pattern in file.lower():
                    pattern_ok = False
                    break
            file_name, file_extension = os.path.splitext(file)
            filetype_ok = file_extension.lower() in ALLOWED_FILETYPES

            upload_files.append(UploadFile(file_name=file,
                                           file_type=file_extension.lower(),
                                           absolute_path=file_path,
                                           relative_path=os.path.relpath(file_path, common_prefix),
                                           allowed=pattern_ok and filetype_ok,
                                           mime_type=mimetypes.guess_type(file_path)[0]))
    return upload_files

def yes_no_question(question: str) -> bool:
    while True:
        answer = input(question + " (y/n)").lower().strip()
        if answer == "y":
            return True
        elif answer == "n":
            return False
        else:
            print("enter either y or n")

def remove_duplicate_by_filename(upload_files: List[UploadFile]):
    file_names = []
    for upload_file in upload_files:
        if upload_file.file_name in file_names:
            upload_file.allowed = False
        else:
            file_names.append(upload_file.file_name)

def main():
    """
    Demonstrates how to add a local directory to a given MyGPT knowledge-base
    """

    # ------------------------------------
    # 1. get list of files
    # ------------------------------------
    upload_files = UploadFiles()
    upload_files.upload_files = walk_directory(path=BASE_PATH, base_path=BASE_PATH)
    zip_files = [x for x in upload_files.upload_files if x.file_type == ".zip"]
    if len(zip_files) > 0:
        if yes_no_question(f"found {len(zip_files)} - unzip them?"):
            for zip_file in zip_files:
                with zipfile.ZipFile(zip_file.absolute_path, "r") as zip_ref:
                    folder, filename = os.path.split(zip_file.absolute_path)
                    folder_name, ext = os.path.splitext(filename)
                    zip_ref.extractall(os.path.join(folder, folder_name))
            upload_files.upload_files = walk_directory(path=BASE_PATH, base_path=BASE_PATH)

    file_names = [f.file_name for f in upload_files.upload_files if f.allowed]
    duplicate_file_names = set([x for x in file_names if file_names.count(x) > 1])
    if len(duplicate_file_names) > 0:
        print(f"duplicated file_names: {len(duplicate_file_names)}")
        if yes_no_question("do hash comparison?"):
            true_duplicates = set()
            for duplicate_file_name in duplicate_file_names:
                duplicate_files = [f for f in upload_files.upload_files if f.allowed and f.file_name == duplicate_file_name]
                hashes = {}
                for duplicate_file in duplicate_files:
                    if duplicate_file.get_hash() in hashes.keys():
                        hashes[duplicate_file.get_hash()].append(duplicate_file)
                    else:
                        hashes.update({duplicate_file.get_hash(): [duplicate_file]})
                if len(hashes) == 1:
                    true_duplicates.add(duplicate_file_name)
                for same_hash_list in hashes.values():
                    for i, duplicate_file in enumerate(same_hash_list):
                        if i == 0:
                            continue
                        duplicate_file.allowed = False
            duplicate_file_names = duplicate_file_names.difference(true_duplicates)
            print(f"found {len(true_duplicates)} true duplicates and removed them")

        print(f"duplicated file_names: {len(duplicate_file_names)}")
        if yes_no_question("show duplicates?"):
            duplicate_list = [f for f in upload_files.upload_files if f.allowed and f.file_name in duplicate_file_names]
            duplicate_list.sort(key=lambda f:f.file_name)
            for upload_file in duplicate_list:
                file_size = os.path.getsize(upload_file.absolute_path)
                print(f"Name: {upload_file.file_name}")
                print(f"      Size: {int(file_size/1024)}KB")
                print(f"      Path: {upload_file.relative_path}")
                print(f"      Hash:{upload_file.get_hash()}")

        if yes_no_question("remove duplicates?"):
            remove_duplicate_by_filename(upload_files.upload_files)
# FIXME: ignored stimmt nicht wenn keine duplicates removed werden
    ignored_filetypes = {}
    used_filetypes = {}
    for upload_file in upload_files.upload_files:
        if upload_file.allowed:
            if upload_file.file_type in used_filetypes.keys():
                used_filetypes[upload_file.file_type] += 1
            else:
                used_filetypes.update({upload_file.file_type: 1})
        else:
            if upload_file.file_type in ignored_filetypes.keys():
                ignored_filetypes[upload_file.file_type] += 1
            else:
                ignored_filetypes.update({upload_file.file_type: 1})
    print(f"about to index {sum(used_filetypes.values())} files:")
    for filetype, count in used_filetypes.items():
        print(f"  {filetype}: {count}")
    print(f"{sum(ignored_filetypes.values())} files won't be indexed:")
    for filetype, count in ignored_filetypes.items():
        print(f"  {filetype}: {count}")

    upload_files.to_file(FILENAME, pretty=yes_no_question("pretty print?"))

    # fin

if __name__ == "__main__":
    main()
    print("Done")
