from UploadFiles import UploadFile, UploadFiles, UploadFileStatus
import helpers
import MyGPTAPI

APICONFIG = MyGPTAPI.APIConfig()
APICONFIG.from_file("api_config.json")
KB_NAME = "kb name"
FILENAMES = ["old_file.json", "old_file2.json"]
NEW_FILENAME = "reupload.json"


def main():
    api = MyGPTAPI.MyGPTAPI(api_config=APICONFIG)
    kb_id = api.get_kb_id_by_name(KB_NAME)
    if kb_id is None:
        print("KB not found")
        exit(-1)

    upload_files = UploadFiles()
    for filename in FILENAMES:
        temp_upload_files = UploadFiles()
        temp_upload_files.from_file(filename)
        upload_files.add_update_files(temp_upload_files.get_all_update_files())

    new_upload_files = UploadFiles()
    errors = api.get_kb_documents_with_errors(kb_id)
    for error_short, docs in helpers.get_kb_documents_by_error(errors).items():
        if helpers.yes_no_question(f"{len(docs)} errors starting with '{error_short}' - prepare to reupload them?"):
            for doc in docs:
                doc_file = None
                doc_id = doc["id"]
                for upload_file in upload_files.get_all_update_files():
                    if upload_file.document_id == doc_id:
                        doc_file = upload_file
                        break
                if doc_file is not None:
                    doc_file.status = UploadFileStatus.NOT_UPLOADED
                    new_upload_files.add_update_file(doc_file)
                else:
                    print(f"file with id {doc_id} not found")

    new_upload_files.to_file(NEW_FILENAME, True)


if __name__ == "__main__":
    main()
    print("Done")
