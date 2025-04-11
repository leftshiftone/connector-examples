from UploadFiles import UploadFiles
import MyGPTAPI

USER = ""
PASSWORD = ""
TENANT_ID = ""
API_URL = "https://api.myg.pt/api/v1"
KB_NAME = ""

ERROR_MESSAGES = ["Workbook is encrypted"]
UPLOAD_FILE = ""


def main():
    api = MyGPTAPI.MyGPTAPI(USER, PASSWORD, API_URL, TENANT_ID)
    kb_id = api.get_kb_id_by_name(KB_NAME)
    if kb_id is None:
        print("KB not found")
        exit(-1)

    errors = api.get_kb_documents_with_errors(kb_id)
    error_ids = [d for d, e in errors]

    upload_files = UploadFiles()
    upload_files.from_file(UPLOAD_FILE)
    for upload_file in upload_files.get_files_for_upload():
        if upload_file.document_id in error_ids:
            print(f"deleting document {upload_file.file_name}")
            api.delete_kb_document(kb_id, upload_file.document_id)

    for doc_id, error_name in errors:
        if error_name in ERROR_MESSAGES:
            print(f"deleting document with id {doc_id}")
            api.delete_kb_document(kb_id, doc_id)


if __name__ == "__main__":
    main()
    print("Done")
