import time

import requests
from azure.storage.blob import BlobClient, ContentSettings
from dataclasses import dataclass, field
import os
from typing import List
import mimetypes
import uuid

USER = "someuser@local"
PASSWORD = "???"
TENANT_ID = "a-tenant"
API_URL = "https://xyz.myg.pt/api/v1"
KB_ID = "fec26cc4-3318-4ba9-bb06-6d429c6a2741"

BASE_PATH = "somewhere/here"
ALLOWED_FILETYPES = [".pdf", ".docx", ".txt", ".pptx", ".xlsx", ".xls", ".doc"]
IGNORE_PATTERNS = ["~$"]

def new_random_uuid() -> str:
    return str(uuid.uuid4())

@dataclass
class UploadFile:
    file_name: str
    file_type: str
    absolute_path: str
    relative_path: str
    allowed: bool
    mime_type: str
    status: str = "not uploaded"
    document_id: str = field(default_factory=new_random_uuid)

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


def main():
    """
    Demonstrates how to add a local directory to a given MyGPT knowledge-base
    """

    # ------------------------------------
    # 1. get list of files
    # ------------------------------------
    upload_files = walk_directory(path=BASE_PATH, base_path=BASE_PATH)
    ignored_filetypes = {}
    used_filetypes = {}
    for upload_file in upload_files:
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
    input("Press enter to start indexing")
    print("started indexing")

    # ------------------------------------
    # 2. acquire a mygpt bearer token
    # ------------------------------------
    bearer_token_response = requests.post(f"{API_URL}/login", json={
        "email": USER,
        "password": PASSWORD,
        "tenant_id": TENANT_ID
    })
    bearer_token_response.raise_for_status()
    bearer_token = bearer_token_response.json()["access_token"]

    # ------------------------------------
    # 3. repeat for all files
    # ------------------------------------

    for upload_file in upload_files:
        if not upload_file.allowed:
            continue
        # ------------------------------------
        # 4. read file
        # ------------------------------------
        with open(upload_file.absolute_path, "rb") as f:
            file_content = f.read()
            if file_content is None:
                upload_file.status = "empty"
                continue

            # ------------------------------------
            # 5. acquire an upload url and the corresponding storage key
            # ------------------------------------
            upload_url_response = requests.get(
                f"{API_URL}/knowledge-bases/{KB_ID}/documents/upload-url?doc_id={upload_file.document_id}",
                headers={"Authorization": f"Bearer {bearer_token}"},
            )
            upload_url_response.raise_for_status()
            upload_url_response_json = upload_url_response.json()
            upload_url = upload_url_response_json["url"]
            upload_storage_key = upload_url_response_json["storage_key"]

            # ------------------------------------
            # 6. upload the file content to the provided upload-url
            #    using Azure Blob Client
            # ------------------------------------
            blob_client = BlobClient.from_blob_url(blob_url=upload_url)

            # note: be aware that the content-type should be set accordingly - otherwise
            # downloads may not work as intended
            blob_client.upload_blob(file_content, content_settings=ContentSettings(content_type=f"{upload_file.mime_type}"), overwrite=True)


            # ------------------------------------
            # 7. send an indexing request
            #    note: indexing is an asynchronous process
            #    meaning a success response here only indicates that the indexing process will start
            # ------------------------------------
            trigger_indexing_response = requests.post(
                url=f"{API_URL}/knowledge-bases/{KB_ID}/documents",
                headers={"Authorization": f"Bearer {bearer_token}"},
                json={
                    "doc_id": upload_file.document_id, #unique identifier of the document
                    "storage_key": upload_storage_key,
                    "original_path": upload_file.relative_path.replace("\\", "/"), #the path (or name) or the file
                    "mime_type": upload_file.mime_type,
                    "size_in_bytes": len(file_content),
                    "meta": {
                        "hash": None, #optional
                        "etag": None, # optional
                        "origin_url": None # optional
                    }
                },
            )
            trigger_indexing_response.raise_for_status()
            print(f"starting indexing for '{upload_file.relative_path}'")
        upload_file.status = "indexing"

        # ------------------------------------
        # 8. wait before next upload to avoid system load
        # ------------------------------------
        time.sleep(60)
    # fin

if __name__ == "__main__":
    main()
    print("Done")
