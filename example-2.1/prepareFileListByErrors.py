import os
import MyGPTAPI
import helpers
from UploadFiles import UploadFile, UploadFiles, UploadFileStatus

APICONFIG = MyGPTAPI.APIConfig()
APICONFIG.from_file("config.json")
KB_NAME = "KB Name"
BASE_PATH = "C:\\a\\b"
FILENAME = "reupload.json"


def main():
    api = MyGPTAPI.MyGPTAPI(api_config=APICONFIG)
    kb_id = api.get_kb_id_by_name(KB_NAME)
    if kb_id is None:
        print("kb name not found")
        exit(-1)

    upload_files = UploadFiles()
    errors = api.get_kb_documents_with_errors(kb_id)
    print(f"found {len(errors)} erroneous documents")
    for error_short, docs in helpers.get_kb_documents_by_error(errors).items():
        if helpers.yes_no_question(f"{len(docs)} errors starting with '{error_short}' - use them?"):
            for doc in docs:
                doc_path = os.path.join(BASE_PATH, doc["original_path"])
                if not os.path.exists(doc_path):
                    print(f"ERROR path not found {doc_path}")
                    continue
                folder_path, file_name = os.path.split(doc_path)
                file_name_wo_ext, file_extension = os.path.splitext(file_name)
                upload_files.add_update_file(UploadFile(file_name=file_name,
                                                         file_type=file_extension.lower(),
                                                         absolute_path=doc_path,
                                                         relative_path=doc["original_path"],
                                                         allowed=True,
                                                         status=UploadFileStatus.NOT_UPLOADED,
                                                         mime_type=doc["mime_type"]))

                upload_files.to_file(filename=FILENAME, pretty=True)

                if __name__ == "__main__":
                    main()
                print("Done")
