from typing import List, Dict
from dataclasses import dataclass, field, asdict
import uuid
import json
import hashlib

def new_random_uuid() -> str:
    return str(uuid.uuid4())

@dataclass
class UploadFile:
    file_name: str
    file_type: str
    absolute_path: str
    relative_path: str
    allowed: bool
    mime_type: str
    status: str = "not uploaded"
    document_id: str = field(default_factory=new_random_uuid)
    hash: str = ""

    def to_dict(self):
        return {k: v for k, v in asdict(self).items()}

    def get_hash(self):
        if self.hash == "":
            with open(self.absolute_path, mode="rb", buffering=0) as file:
                self.hash = hashlib.file_digest(file, 'sha256').hexdigest()
        return self.hash


class UploadFiles:
    def __init__(self):
        self.upload_files: List[UploadFile] = []

    def to_file(self, filename, pretty: bool = False):
        json_list = [uf.to_dict() for uf in self.upload_files]
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
                    param_list.append(data[param])
                upload_file = UploadFile(*param_list)
                if isinstance(upload_file.allowed, str):
                    upload_file.allowed = eval(upload_file.allowed)
                self.upload_files.append(upload_file)

    def get_files_for_upload(self) -> List[UploadFile]:
        return [uf for uf in self.upload_files if uf.allowed]

