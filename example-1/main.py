import requests
from azure.storage.blob import BlobClient
import os
import uuid
import mimetypes

USER = "admin@local"
PASSWORD = "!c6TBf^3H7w#DM2N!DnWx6HM"
TENANT_ID = "test"
API_URL = "https://beta.api.mygpt.leftshiftone.com/api/v1"
KB_ID = "411cf2b7-1e16-41f4-82dd-e8310b64e82b"

FILE2UPLOAD = "C:\\Users\\ChristofSteinkellner\\Downloads\\MyGPT Insights 20250302 20250401.csv"


def main():
    """
    Demonstrates how to add a local file to a given MyGPT knowledge-base
    """

    # ------------------------------------
    # 1. read a local file
    # ------------------------------------
    file_path = FILE2UPLOAD
    path, file_name = os.path.split(file_path)
    if file_name.endswith(".csv") and False:
        mime_type = "text/csv"
    else:
        mime_type, encoding = mimetypes.guess_type(file_path)
    file_content = None
    with open(file_path, "rb") as f:
        file_content = f.read()

    assert file_content is not None

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
    # 3. acquire an upload url and the corresponding storage key
    # ------------------------------------
    document_id = str(uuid.uuid4())
    upload_url_response = requests.get(
        f"{API_URL}/knowledge-bases/{KB_ID}/documents/upload-url?doc_id={document_id}",
        headers={"Authorization": f"Bearer {bearer_token}"},
    )
    upload_url_response.raise_for_status()
    upload_url_response_json = upload_url_response.json()
    upload_url = upload_url_response_json["url"]
    upload_storage_key = upload_url_response_json["storage_key"]

    # ------------------------------------
    # 4. upload the file content to the provided upload-url
    #    using Azure Blob Client
    # ------------------------------------
    blob_client = BlobClient.from_blob_url(blob_url=upload_url)
    blob_client.upload_blob(file_content, overwrite=True)


    # ------------------------------------
    # 5. send an indexing request
    #    note: indexing is an asynchronous process
    #    meaning a success response here only indicates that the indexing process will start
    # ------------------------------------
    trigger_indexing_response = requests.post(
        url=f"{API_URL}/knowledge-bases/{KB_ID}/documents",
        headers={"Authorization": f"Bearer {bearer_token}"},
        json={
            "doc_id": document_id, #unique identifier of the document
            "storage_key": upload_storage_key,
            "original_path": file_name, #the path (or name) or the file
            "mime_type": mime_type,
            "size_in_bytes": len(file_content),
            "meta": {
                "hash": None, #optional
                "etag": None, # optional
                "origin_url": None, # optional
                "properties": {
                    # add custom properties here!, but never user hash, etag or origin_url
                }
            }

        },
    )
    trigger_indexing_response.raise_for_status()
    # fin

if __name__ == "__main__":
    main()
