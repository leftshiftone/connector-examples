import datetime
from typing import List, Dict
import requests
import json
from dataclasses import dataclass
import logging
from dateutil import parser


@dataclass
class APIConfig:
    user: str = "username"
    password: str = "******"
    api_url: str = "https://xyz.myg.pt/api/v1"
    tenant_id: str = "tenant"

    def from_file(self, filename):
        with open(filename, mode="r", encoding="utf-8") as file:
            json_data = json.load(file)
            for key, value in json_data.items():
                self.__setattr__(key, value)


class MyGPTAPI:
    def __init__(self, api_config: APIConfig):
        self.api_config = api_config
        bearer_token_response = requests.post(f"{self.api_config.api_url}/login", json={
            "email": self.api_config.user,
            "password": self.api_config.password,
            "tenant_id": self.api_config.tenant_id
        })
        bearer_token_response.raise_for_status()
        self.auth = bearer_token_response.json()["access_token"]
        self.__logger = logging.getLogger("MyGPTAPI")

    def __get_auth(self):
        return self.auth  # just for refactoring later

    def get_kb_ids(self) -> [(str, str)]:
        kb_response = requests.get(f"{self.api_config.api_url}/knowledge-bases",
                                   headers={"Authorization": f"Bearer {self.__get_auth()}"})
        kb_response.raise_for_status()
        kb_response_json = kb_response.json()
        kbs = []
        for kb_data in kb_response_json:
            kbs.append((kb_data["id"], kb_data["name"]))
        return kbs

    def get_kb_id_by_name(self, kb_name: str):
        for kb_id_temp, kb_name_temp in self.get_kb_ids():
            if kb_name == kb_name_temp:
                return kb_id_temp
        return None

    def get_kb_documents(self, kb_id: str, offset: int = 0, limit: int = 100) -> List[Dict]:
        response = requests.get(
            f"{self.api_config.api_url}/knowledge-bases/{kb_id}/documents?offset={offset}&limit={limit}&sort_by=status&sort_direction=ASC",
            headers={"Authorization": f"Bearer {self.__get_auth()}"})
        response.raise_for_status()
        return [e for e in response.json()["elements"]]

    def get_latest_changed_kb_documents(self, kb_id: str, duration: datetime.timedelta = datetime.timedelta(hours=1),
                                        batch_size: int = 100) -> (List[Dict], int):
        now = datetime.datetime.now().astimezone()
        total = None
        documents = []
        start = 0
        batch_size = 100
        while len(documents) == 0 or len(documents) >= total:
            response = requests.get(
                f"{self.api_config.api_url}/knowledge-bases/{kb_id}/documents?offset={start}&limit={start + batch_size}&sort_by=updated_at&sort_direction=DESC",
                headers={"Authorization": f"Bearer {self.__get_auth()}"})
            response.raise_for_status()
            if total is None:
                total = response.json()["total"]
            break_loop = False
            for e in response.json()["elements"]:
                if (now - parser.parse(e["updated_at"])) < duration:
                    documents.append(e)
                else:
                    break_loop = True
            if break_loop:
                break
            start += batch_size
        return documents, total

    def get_kb_document_count(self, kb_id: str):
        response = requests.get(
            f"{self.api_config.api_url}/knowledge-bases/{kb_id}/documents?offset={0}&limit={1}&sort_by=status&sort_direction=ASC",
            headers={"Authorization": f"Bearer {self.__get_auth()}"})
        response.raise_for_status()
        return response.json()["total"]

    def get_all_kb_documents(self, kb_id: str, max_docs: int = None) -> List[dict]:
        if max_docs is None:
            max_docs = 1 << 32
        documents = []
        start = 0
        block_size = 100
        while True:
            tmp_documents = self.get_kb_documents(kb_id=kb_id, offset=start, limit=block_size)
            documents.extend(tmp_documents)
            if len(tmp_documents) >= block_size and max_docs > len(documents):
                start += block_size
            else:
                break
        return documents

    def get_all_kb_documents_not_in_success(self, kb_id: str) -> List[dict]:
        documents = []
        start = 0
        block_size = 100
        while True:
            tmp_documents = self.get_kb_documents(kb_id=kb_id, offset=start, limit=block_size)
            documents.extend(tmp_documents)
            if tmp_documents[len(tmp_documents) - 1]["status"] == "success":
                break
            start += block_size
        return documents

    def get_kb_documents_with_errors(self, kb_id: str, max_docs: int = None) -> List[dict]:
        documents = self.get_all_kb_documents(kb_id=kb_id, max_docs=max_docs)
        return [e for e in documents if e["status"] == "failed"]

    def check_for_document_status(self, knowledgebase_name: str = None):
        for kb_id, kb_name in self.get_kb_ids():
            if knowledgebase_name is not None and knowledgebase_name != kb_name:
                continue
            states = {}
            documents = self.get_all_kb_documents_not_in_success(kb_id=kb_id)
            for data in documents:
                try:
                    states[data["status"]] += 1
                except KeyError:
                    states.update({data["status"]: 1})
            try:
                failed = states["failed"]
            except KeyError:
                failed = 0
            str_states = []
            for status, count in states.items():
                if status != "success":
                    str_states.append((status, count))
            if len(str_states) > 0:
                self.__logger.info(f"State for KB {kb_name}")
                for status, count in str_states:
                    self.__logger.info(f"  {str(count).rjust(5)} {status}")
            total = self.get_kb_document_count(kb_id)
            self.__logger.info(f"  {str(total).rjust(5)} total")
            if failed > 0:
                self.__logger.info(f"  failed rate: {round(failed / total * 100, 2)} %")

    def delete_kb_document(self, kb_id: str, doc_id: str):
        response = requests.delete(f"{self.api_config.api_url}/knowledge-bases/{kb_id}/documents/{doc_id}",
                                   headers={"Authorization": f"Bearer {self.__get_auth()}"})
        response.raise_for_status()

    def reindex_kb_documents(self, kb_id: str, doc_ids: List[str]):
        response = requests.post(f"{self.api_config.api_url}/knowledge-bases/{kb_id}/documents/reindex",
                                 headers={"Authorization": f"Bearer {self.__get_auth()}"},
                                 data=json.dumps({"doc_ids": doc_ids}))
        response.raise_for_status()
