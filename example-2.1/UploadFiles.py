from typing import List, Dict
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
import json
import hashlib

def new_random_uuid() -> str:
    return str(uuid.uuid4())


class UploadFileStatus(Enum):
    WRONG_TYPE = "wrong type"
    NOT_UPLOADED = "not uploaded"
    DUPLICATE = "Duplicate"
    INDEXING = "indexing"
    EMPTY = "empty"

@dataclass
class UploadFile:
    file_name: str
    file_type: str
    absolute_path: str
    relative_path: str
    allowed: bool
    mime_type: str
    status: UploadFileStatus = UploadFileStatus.NOT_UPLOADED
    document_id: str = field(default_factory=new_random_uuid)
    hash: str = ""

    def to_dict(self):
        dict_repr = {}
        for k, v in asdict(self).items():
            if isinstance(v, UploadFileStatus):
                dict_repr.update({k: v.value})
            else:
                dict_repr.update({k: v})
        return dict_repr

    def get_hash(self):
        if self.hash == "":
            with open(self.absolute_path, mode="rb", buffering=0) as file:
                self.hash = hashlib.file_digest(file, 'sha256').hexdigest()
        return self.hash


class UploadFiles:
    def __init__(self):
        self.upload_files: Dict[str, UploadFile] = {}

    def add_update_file(self, update_file: UploadFile):
        self.upload_files.update({update_file.document_id: update_file})

    def add_update_files(self, update_files: List[UploadFile]):
        for uf in update_files:
            self.add_update_file(uf)

    def get_update_file_by_id(self, doc_id: str) -> UploadFile:
        return self.upload_files[doc_id]

    def get_all_update_files(self) -> List[UploadFile]:
        return list(self.upload_files.values())

    def to_file(self, filename, pretty: bool = False):
        json_list = [uf.to_dict() for uf in self.get_all_update_files()]
        with open(filename, mode="w", encoding="utf-8") as file:
            if pretty:
                json.dump(json_list, file, ensure_ascii=False, indent=4)
            else:
                json.dump(json_list, file, ensure_ascii=False)

    def from_file(self, filename):
        with open(filename, mode="r", encoding="utf-8") as file:
            json_data = json.load(file)
            for data in json_data:
                param_list = []
                for param in UploadFile.__annotations__:
                    try:
                        if param == "status":
                            param_list.append(UploadFileStatus(data[param]))
                        else:
                            param_list.append(data[param])
                    except KeyError:
                        pass
                upload_file = UploadFile(*param_list)
                if isinstance(upload_file.allowed, str):
                    upload_file.allowed = eval(upload_file.allowed)
                self.add_update_file(upload_file)

    def get_files_for_upload(self) -> List[UploadFile]:
        return [uf for uf in self.get_all_update_files() if uf.allowed and uf.status == UploadFileStatus.NOT_UPLOADED]

    def remove_hash_duplicates(self) -> int:
        hashes = {}
        for upload_file in self.get_all_update_files():
            if upload_file.status == UploadFileStatus.DUPLICATE:
                continue
            try:
                hashes[upload_file.get_hash()].append(upload_file)
            except KeyError:
                hashes.update({upload_file.get_hash(): [upload_file]})
        duplicates = 0
        for same_file_list in hashes.values():
            for upload_file in same_file_list[1:]:
                upload_file.status = UploadFileStatus.DUPLICATE
                duplicates += 1
        return duplicates


