import time
import MyGPTAPI
import helpers
from UploadFiles import UploadFiles, UploadFileStatus

APICONFIG = MyGPTAPI.APIConfig()
APICONFIG.from_file("api_config.json")
KB_NAME = "KB Name"

# if true the upload file can be updated, so that the files can be re-uploaded
UPDATE_JSON = False
FILENAME = "index_errors.json"
MAX_DOCS = 1000  # set to 1 << 32, if no limit
MAX_DELETES = 1000
PAUSE = 5

def main():
    upload_files = UploadFiles()
    if UPDATE_JSON:
        upload_files.from_file(FILENAME)

    api = MyGPTAPI.MyGPTAPI(api_config=APICONFIG)
    kb_id = api.get_kb_id_by_name(KB_NAME)
    if kb_id is None:
        print("KB not found")
        exit(-1)

    del_docs = 0
    errors = api.get_kb_documents_with_errors(kb_id, max_docs=MAX_DOCS)
    docs2delete = []
    for error_short, docs in helpers.get_kb_documents_by_error(errors).items():
        if helpers.yes_no_question(f"{len(docs)} errors starting with '{error_short}' - delete them?"):
            docs2delete.extend(docs)

        if len(docs2delete) >= MAX_DELETES:
            break
    for doc in docs2delete:
        print(f"deleting document {doc["original_path"]}")
        api.delete_kb_document(kb_id=kb_id, doc_id=doc["id"])
        if UPDATE_JSON:
            try:
                upload_files.get_update_file_by_id(doc["id"]).status = UploadFileStatus.NOT_UPLOADED
            except KeyError:
                print(f"id {doc["id"]}, name {doc["original_path"]} not found in JSON")
        del_docs += 1
        time.sleep(PAUSE)
        if del_docs >= MAX_DELETES:
            break

    if UPDATE_JSON:
        upload_files.to_file(FILENAME)



if __name__ == "__main__":
    main()
    print("Done")
