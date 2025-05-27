import MyGPTAPI
from UploadFiles import UploadFiles, UploadFileStatus, new_random_uuid

FILENAME = "upload_files.json"
FILENAME_NEW = "upload_files_new.json"
KB_NAME = "KB Name"
api_config = MyGPTAPI.APIConfig()
api_config.from_file("api_config.json")

RANDOMIZE_DOCUMENT_IDS = False

update_files = UploadFiles()
update_files.from_file(FILENAME)

api = MyGPTAPI.MyGPTAPI(api_config=api_config)
kb_id = api.get_kb_id_by_name(KB_NAME)
if kb_id is None:
    print("kb name not found")
    exit(-1)
all_documents = api.get_all_kb_documents(kb_id)
print(f"got {len(all_documents)} documents")

changed_to_indexed = 0
changed_to_not_uploaded = 0
doc_map = {doc["original_path"]: doc for doc in all_documents}
for update_file in update_files.get_all_update_files():
    document = None
    linux_path = update_file.relative_path.replace("\\", "/")
    try:
        doc = doc_map[linux_path]
        update_file.status = UploadFileStatus.INDEXING
        update_file.document_id = doc["id"]
        changed_to_indexed += 1
        doc.update({"found": True})
        index_file_found = True
    except KeyError:
        update_file.status = UploadFileStatus.NOT_UPLOADED
        if RANDOMIZE_DOCUMENT_IDS:
            update_file.document_id = new_random_uuid()
        changed_to_not_uploaded += 1

print(f"changed to indexed: {changed_to_indexed}")
print(f"changed to not uploaded: {changed_to_not_uploaded}")

print("missing, but indexed:")
for doc in [d for d in all_documents if "found" not in d.keys()]:
    print(str(doc))

new_upload_files = UploadFiles()
new_upload_files.add_update_files(update_files.get_files_for_upload())
new_upload_files.to_file(FILENAME_NEW, True)
