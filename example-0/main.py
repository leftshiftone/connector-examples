import json

import requests
from azure.storage.blob import BlobClient
from requests.auth import HTTPBasicAuth


USERNAME = "admin"
PASSWORD = "???"
BASE_URL = "https://???/api/v1"
FILE_TO_UPLOAD_PATH = "/tmp/xyz.zip"

def main():
    # first acquire the azure blob storage upload url
    auth = HTTPBasicAuth(username=USERNAME,
                         password=PASSWORD)
    upload_url_resp = requests.get(f"{BASE_URL}/upload-url",
                                   auth=auth)
    upload_url_json = json.loads(upload_url_resp.content.decode("utf-8"))
    upload_url = upload_url_json["url"]

    print("Acquired presigned upload URL")

    # once the url has been acquired the file can be uploaded using azure blob client
    blob_client = BlobClient.from_blob_url(upload_url)
    with open(FILE_TO_UPLOAD_PATH, mode="rb") as f:
        blob_client.upload_blob(data=f.read())

    print("File uploaded")

    # after the successful upload the original body from the first request
    # must be sent to initiate the processing pipeline for a given language (selected by using the correct path parameter)
    requests.post(f"{BASE_URL}/de/process", # german
                  json=upload_url_json,
                  auth=auth)

    # requests.post(f"{BASE_URL}/en/process", # english
    #               json=upload_url_json,
    #               auth=auth)

    print("Processing pipeline started - check MyGPT knowledge base for updates")

if __name__ == '__main__':
    main()