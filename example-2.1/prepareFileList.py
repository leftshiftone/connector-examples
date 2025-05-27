import os
from typing import List, Set
import mimetypes
import zipfile
from helpers import yes_no_question

from UploadFiles import UploadFile, UploadFiles, UploadFileStatus

BASE_PATH = "somewhere/here"
ALLOWED_FILETYPES = [".pdf", ".docx", ".txt", ".pptx", ".xlsx", ".xls", ".doc"]
IGNORE_PATTERNS = ["~$", "~�"]
IGNORE_FOLDER_NAMES = ["__MACOSX", "Archiv", "Archive", "00_Archiv"]  # explicitly ignores folder by name
IGNORE_FOLDER_PATTERNS = ["archiv"]  # ignores all folders containing this name, but prompts each folder
FILENAME = "update_files.json"


def walk_directory(path: str, base_path: str) -> List[UploadFile]:
    upload_files: List[UploadFile] = []
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        common_prefix = os.path.commonprefix([path, base_path])
        if os.path.isdir(file_path):
            ignore = str(file).lower() in [n.lower() for n in IGNORE_FOLDER_NAMES]
            if not ignore:
                for ignore_folder_pattern in IGNORE_FOLDER_PATTERNS:
                    if ignore_folder_pattern in str(file).lower():
                        ignore = True
                        break
                if ignore:
                    ignore = yes_no_question(f"ignore path '{file_path}'?")
            if not ignore:
                upload_files.extend(walk_directory(path=file_path, base_path=base_path))
        else:
            pattern_ok = True
            for pattern in IGNORE_PATTERNS:
                if pattern in file.lower():
                    pattern_ok = False
                    break
            if not pattern_ok:
                continue
            file_name, file_extension = os.path.splitext(file)
            filetype_ok = file_extension.lower() in ALLOWED_FILETYPES

            upload_status = UploadFileStatus.NOT_UPLOADED
            if not (pattern_ok and filetype_ok):
                upload_status = UploadFileStatus.WRONG_TYPE
            upload_files.append(UploadFile(file_name=file,
                                           file_type=file_extension.lower(),
                                           absolute_path=file_path,
                                           relative_path=os.path.relpath(file_path, common_prefix),
                                           allowed=pattern_ok and filetype_ok,
                                           status=upload_status,
                                           mime_type=mimetypes.guess_type(file_path)[0]))
    return upload_files


def remove_duplicate_by_filename(upload_files: List[UploadFile], duplicate_names: Set[str]):
    file_names = []
    for upload_file in upload_files:
        if upload_file.file_name not in duplicate_names:
            continue
        if upload_file.file_name in file_names:
            upload_file.allowed = False
            upload_file.status = UploadFileStatus.DUPLICATE
        else:
            file_names.append(upload_file.file_name)

def remove_similar_file_names(upload_files: UploadFiles):
    relative_paths = {}
    for upload_file in upload_files.get_all_update_files():
        if upload_file.allowed:
            rel_path, ext = os.path.splitext(upload_file.relative_path)
            try:
                relative_paths[rel_path].append(upload_file)
            except KeyError:
                relative_paths.update({rel_path: [upload_file]})

    duplicate_size = 0
    duplicates = 0
    for rel_path, upload_file_list in relative_paths.items():
        if len(upload_file_list) == 1:
            continue
        changes = [(upload_file, os.path.getmtime(upload_file.absolute_path)) for upload_file in upload_file_list]
        changes.sort(key=lambda x: x[1], reverse=True)
        for upload_file, changedate in changes[1:]:
            upload_file.status = UploadFileStatus.DUPLICATE
            duplicate_size += os.path.getsize(upload_file.absolute_path)
            duplicates += 1

    print(f"duplicates: {duplicates}")
    print(f"size: {duplicate_size >> 20} MB")


def main():
    """
    Demonstrates how to add a local directory to a given MyGPT knowledge-base
    """

    # ------------------------------------
    # 1. get list of files
    # ------------------------------------
    upload_files = UploadFiles()
    upload_files.add_update_files(walk_directory(path=BASE_PATH, base_path=BASE_PATH))
    zip_files = [x for x in upload_files.get_all_update_files() if x.file_type == ".zip"]
    if len(zip_files) > 0:
        print(f"found {len(zip_files)} zip files")
        for zip_file in zip_files:
            print(f"  {zip_file.relative_path}")
        if yes_no_question(f"found {len(zip_files)} zip files - unzip them?"):
            for zip_file in zip_files:
                with zipfile.ZipFile(zip_file.absolute_path, "r") as zip_ref:
                    folder, filename = os.path.split(zip_file.absolute_path)
                    folder_name, ext = os.path.splitext(filename)
                    extract_path = os.path.join(folder, folder_name)
                    zip_ref.extractall(extract_path)
                    upload_files.add_update_files(walk_directory(path=extract_path, base_path=BASE_PATH))

    file_names_dict = {}
    for upload_file in upload_files.get_all_update_files():
        if upload_file.allowed:
            try:
                file_names_dict[upload_file.file_name] += 1
            except KeyError:
                file_names_dict.update({upload_file.file_name: 1})
    duplicate_file_names = []
    for file_name, count in file_names_dict.items():
        if count > 1:
            duplicate_file_names.append(file_name)
    duplicate_file_names = set(duplicate_file_names)
    if len(duplicate_file_names) > 0:
        print(f"duplicated file_names: {len(duplicate_file_names)}")
        if yes_no_question("do hash comparison?"):
            true_duplicates = set()
            for duplicate_file_name in duplicate_file_names:
                duplicate_files = [f for f in upload_files.get_all_update_files() if
                                   f.allowed and f.file_name == duplicate_file_name]
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
                        duplicate_file.status = UploadFileStatus.DUPLICATE
            duplicate_file_names = duplicate_file_names.difference(true_duplicates)
            print(f"found {len(true_duplicates)} true duplicates and removed them")

        print(f"duplicated file_names: {len(duplicate_file_names)}")
        if yes_no_question("show duplicates?"):
            duplicate_list = [f for f in upload_files.get_all_update_files() if f.allowed and f.file_name in duplicate_file_names]
            duplicate_list.sort(key=lambda f: f.file_name)
            for upload_file in duplicate_list:
                file_size = os.path.getsize(upload_file.absolute_path)
                print(f"Name: {upload_file.file_name}")
                print(f"      Size: {int(file_size / 1024)}KB")
                print(f"      Path: {upload_file.relative_path}")
                print(f"      Hash:{upload_file.get_hash()}")

        if yes_no_question("remove duplicates?"):
            remove_duplicate_by_filename(upload_files.get_all_update_files(), duplicate_file_names)

    if yes_no_question("check for hash duplicates?"):
        duplicates = upload_files.remove_hash_duplicates()
        print(f"found {duplicates} true duplicates and removed them")

    if yes_no_question("check for similar files (e.g. abc.pdf and abc.doc in same folder)?"):
        remove_similar_file_names(upload_files)

    ignored_filetypes = {}
    used_filetypes = {}
    size_used = 0
    for upload_file in upload_files.get_all_update_files():
        if upload_file.allowed:
            size_used += os.path.getsize(upload_file.absolute_path)
            if upload_file.file_type in used_filetypes.keys():
                used_filetypes[upload_file.file_type] += 1
            else:
                used_filetypes.update({upload_file.file_type: 1})
        else:
            if upload_file.status == UploadFileStatus.DUPLICATE:
                continue
            if upload_file.file_type in ignored_filetypes.keys():
                ignored_filetypes[upload_file.file_type] += 1
            else:
                ignored_filetypes.update({upload_file.file_type: 1})
    print(f"about to index {sum(used_filetypes.values())} files:")
    for filetype, count in used_filetypes.items():
        print(f"  {filetype}: {count}")
    print(f"total size: {size_used >> 20} MB")
    print(f"{sum(ignored_filetypes.values())} files won't be indexed:")
    for filetype, count in ignored_filetypes.items():
        print(f"  {filetype}: {count}")

    upload_files.to_file(FILENAME, pretty=yes_no_question("pretty print?"))

    # fin


if __name__ == "__main__":
    main()
    print("Done")
