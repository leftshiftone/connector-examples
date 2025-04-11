from UploadFiles import UploadFile, UploadFiles
import MyGPTAPI

USER = ""
PASSWORD = ""
TENANT_ID = ""
API_URL = "https://api.myg.pt/api/v1"
KB_NAME = ""
FILENAMES = []
NEW_FILENAME = "upload.json"

def yes_no_question(question: str) -> bool:
    while True:
        answer = input(question + " (y/n)").lower().strip()
        if answer == "y":
            return True
        elif answer == "n":
            return False
        else:
            print("enter either y or n")

def main():
    api = MyGPTAPI.MyGPTAPI(USER, PASSWORD, API_URL, TENANT_ID)
    kb_id = api.get_kb_id_by_name(KB_NAME)
    if kb_id is None:
        print("KB not found")
        exit(-1)

    upload_files = UploadFiles()
    for filename in FILENAMES:
        temp_upload_files = UploadFiles()
        temp_upload_files.from_file(filename)
        upload_files.upload_files.extend(temp_upload_files.upload_files)

    errors = api.get_kb_documents_with_errors(kb_id)
    error_shorthands = {}
    for doc_id, error_name in errors:
        short = error_name[:16]
        if short in error_shorthands.keys():
            error_shorthands[short].append(error_name)
        else:
            error_shorthands.update({short: [error_name]})

    relevant_errors = []
    for error_name in error_shorthands.keys():
        print(f"error: {error_name}")
        if yes_no_question("reupload this error?"):
            relevant_errors.extend(error_shorthands[error_name])

    for doc_id, error_name in errors:
        if error_name in relevant_errors:
            doc_file = None
            for upload_file in upload_files.upload_files:
                if upload_file.document_id == doc_id:
                    doc_file = upload_file
                    break
            if doc_file is not None:
                doc_file.status = "not uploaded"
            else:
                print(f"file with id {doc_id} not found")

    upload_files.upload_files = [uf for uf in upload_files.upload_files if uf.status == "not uploaded" and uf.allowed]
    upload_files.to_file(NEW_FILENAME, True)


if __name__ == "__main__":
    main()
    print("Done")
