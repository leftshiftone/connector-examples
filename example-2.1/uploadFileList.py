import time

import requests
from azure.storage.blob import BlobClient
from UploadFiles import UploadFile, UploadFiles

USER = "someuser@local"
PASSWORD = "???"
TENANT_ID = "a-tenant"
API_URL = "https://xyz.myg.pt/api/v1"
KB_ID = "fec26cc4-3318-4ba9-bb06-6d429c6a2741"
FILENAME = "update_files.json"


def main():
    """
    Demonstrates how to add a local directory to a given MyGPT knowledge-base
    """

    # ------------------------------------
    # 1. get list of files
    # ------------------------------------
    upload_files = UploadFiles()
    upload_files.from_file(FILENAME)

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

    for upload_file in upload_files.upload_files:
        if not upload_file.allowed or upload_file.status != "not uploaded":
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
            response_blob_client = blob_client.upload_blob(file_content, overwrite=True)

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
        upload_files.to_file(FILENAME)

        # ------------------------------------
        # 8. wait before next upload to avoid system load
        # ------------------------------------
        time.sleep(30)
    # fin

if __name__ == "__main__":
    main()
    print("Done")
