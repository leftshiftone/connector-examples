from typing import List
import requests
import json
from dataclasses import dataclass

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

    def get_kb_documents_with_errors(self, kb_id: str, limit: int = 500) -> List[dict]:
        response = requests.get(
            f"{self.api_config.api_url}/knowledge-bases/{kb_id}/documents?offset=0&limit={limit}&sort_by=status&sort_direction=ASC",
            headers={"Authorization": f"Bearer {self.__get_auth()}"})
        response.raise_for_status()
        return [e for e in response.json()["elements"] if e["status"] == "failed"]

    def check_for_document_status(self, limit: int = 500):
        for kb_id, kb_name in self.get_kb_ids():
            states = {}
            response = requests.get(
                f"{self.api_config.api_url}/knowledge-bases/{kb_id}/documents?offset=0&limit={limit}&sort_by=status&sort_direction=ASC",
                headers={"Authorization": f"Bearer {self.__get_auth()}"})
            response.raise_for_status()
            for data in response.json()["elements"]:
                try:
                    states[data["status"]] += 1
                except KeyError:
                    states.update({data["status"]: 1})
            str_states = []
            for status, count in states.items():
                if status != "success":
                    str_states.append((status, count))
            if len(str_states) > 0:
                print(f"\nState for KB {kb_name}")
                for status, count in str_states:
                    print(f"  {str(count).rjust(3)} {status}")


    def delete_kb_document(self, kb_id: str, doc_id: str):
        response = requests.delete(f"{self.api_config.api_url}/knowledge-bases/{kb_id}/documents/{doc_id}",
                                   headers={"Authorization": f"Bearer {self.__get_auth()}"})
        response.raise_for_status()

    def reindex_kb_documents(self, kb_id: str, doc_ids: List[str]):
        response = requests.post(f"{self.api_config.api_url}/knowledge-bases/{kb_id}/documents/reindex",
                                 headers={"Authorization": f"Bearer {self.__get_auth()}"},
                                 data=json.dumps({"doc_ids": doc_ids}))
        response.raise_for_status()
