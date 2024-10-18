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
    # the response is a text/event-stream containing the progress of the processing pipeline
    # note: the processing pipeline is asynchronous and the response does not indicate the final state of the pipeline
    session = requests.Session()
    language = "de" # or "en"
    with session.post(f"{BASE_URL}/{language}/process", # german
                  json=upload_url_json,
                  auth=auth,
                  stream=True
                  ) as response:
        for line in response.iter_lines():
            if line:
                print(line)

if __name__ == '__main__':
    main()