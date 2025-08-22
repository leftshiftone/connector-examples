import os.path
import time
import threading
from queue import Queue
import requests
from azure.storage.blob import BlobClient
from UploadFiles import UploadFiles, UploadFileStatus
import MyGPTAPI
import helpers

APICONFIG = MyGPTAPI.APIConfig()
APICONFIG.from_file("api_config.json")
KB_NAME = "My KB"
FILENAME = "upload_files.json"
PARALLEL_UPLOADS = 5
PAUSE = 0
MAX_UPLOADS = 10000

MAX_FILE_SIZE = 100 * 1024 ** 2


def upload_threaded(queue: Queue, api: MyGPTAPI.MyGPTAPI, kb_id: str,
                    total_count: int, upload_files: UploadFiles, write_lock: threading.Lock,
                    stop_event: threading.Event):
    while not queue.empty() and not stop_event.is_set():
        i, upload_file = queue.get()

        with open(upload_file.absolute_path, "rb") as f:
            file_content = f.read()
            if file_content is None:
                upload_file.status = UploadFileStatus.EMPTY
                continue

            for retry in range(3):
                try:
                    # ------------------------------------
                    # 5. acquire an upload url and the corresponding storage key
                    # ------------------------------------
                    upload_url_response = requests.get(
                        f"{api.api_config.api_url}/knowledge-bases/{kb_id}/documents/upload-url?doc_id={upload_file.document_id}",
                        headers={"Authorization": f"Bearer {api.auth}"},
                    )
                    upload_url_response.raise_for_status()
                    upload_url_response_json = upload_url_response.json()
                    upload_url = upload_url_response_json["url"]
                    upload_storage_key = upload_url_response_json["storage_key"]

                    # ------------------------------------
                    # 6. upload the file content to the provided upload-url
                    #    using Azure Blob Client
                    # ------------------------------------
                    file_size_mb = os.path.getsize(upload_file.absolute_path) >> 20
                    print(f"({i + 1}/{total_count}) start upload for {upload_file.relative_path} ({file_size_mb}MB)")
                    blob_client = BlobClient.from_blob_url(blob_url=upload_url)
                    response_blob_client = blob_client.upload_blob(file_content, overwrite=True, timeout=1800,
                                                                   connection_timeout=14400)

                    # ------------------------------------
                    # 7. send an indexing request
                    #    note: indexing is an asynchronous process
                    #    meaning a success response here only indicates that the indexing process will start
                    # ------------------------------------
                    trigger_indexing_response = requests.post(
                        url=f"{api.api_config.api_url}/knowledge-bases/{kb_id}/documents",
                        headers={"Authorization": f"Bearer {api.auth}"},
                        json={
                            "doc_id": upload_file.document_id,  # unique identifier of the document
                            "storage_key": upload_storage_key,
                            "original_path": upload_file.relative_path.replace("\\", "/"),
                            # the path (or name) or the file
                            "mime_type": upload_file.mime_type,
                            "size_in_bytes": len(file_content),
                            "meta": {
                                "hash": None,  # optional
                                "etag": None,  # optional
                                "origin_url": None  # optional
                            }
                        },
                    )
                    trigger_indexing_response.raise_for_status()
                    print(f"({i + 1}/{total_count}) starting indexing for '{upload_file.relative_path}'")
                    upload_file.status = UploadFileStatus.INDEXING
                    break
                except Exception as e:
                    print("error happened, try again")
                    print(e)
                    time.sleep(60)
                if stop_event.is_set():
                    break
        with write_lock:
            upload_files.to_file(FILENAME)
        if PAUSE > 0:
            time.sleep(PAUSE)


def stop_thread(stop_event: threading.Event):
    while not stop_event.is_set():
        if helpers.yes_no_question("stop?", stop_event):
            print("about to stop")
            stop_event.set()
    print("stopper thread ended")


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
    api = MyGPTAPI.MyGPTAPI(api_config=APICONFIG)
    kb_id = api.get_kb_id_by_name(KB_NAME)
    if kb_id is None:
        print("kb name not found")
        exit(-1)

    # ------------------------------------
    # 3. repeat for all files
    # ------------------------------------
    files_for_upload = upload_files.get_files_for_upload()
    queue = Queue()
    upload_count = 0
    too_big_files = 0
    for i, upload_file in enumerate(files_for_upload):
        if not upload_file.allowed or upload_file.status != UploadFileStatus.NOT_UPLOADED:
            continue
        if os.path.getsize(upload_file.absolute_path) >= MAX_FILE_SIZE:
            too_big_files += 1
            print(f"size {os.path.getsize(upload_file.absolute_path) >> 20}MB {upload_file.absolute_path}")
            continue
        queue.put((upload_count, upload_file))
        upload_count += 1
        if upload_count >= MAX_UPLOADS:
            break
    if too_big_files > 0:
        print(f"{too_big_files} files ignored due to their size")

    threads = []
    lock = threading.Lock()
    event = threading.Event()
    for i in range(PARALLEL_UPLOADS):
        t = threading.Thread(target=upload_threaded, args=(queue, api, kb_id, upload_count, upload_files, lock, event),
                             daemon=True)
        threads.append(t)
        t.start()

    stopper = threading.Thread(target=stop_thread, args=(event,))
    stopper.start()
    try:
        for t in threads: t.join()
        print("all worker-threads are done")
        print("press enter to stop")
        event.set()
        stopper.join()
    except KeyboardInterrupt:
        print("wait for threads to finish")
        event.set()
        for t in threads: t.join()
        stopper.join()
    # fin

    with lock:
        upload_files.to_file(FILENAME, pretty=True)


if __name__ == "__main__":
    main()
    print("Done")
