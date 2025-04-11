
import requests


class MyGPTAPI:
    def __init__(self, user: str, password: str, api_url: str, tenant_id: str):
        self.__user = user
        self.__password = password
        self.api_url = api_url
        self.tenant_id = tenant_id
        bearer_token_response = requests.post(f"{self.api_url}/login", json={
            "email": self.__user,
            "password": self.__password,
            "tenant_id": tenant_id
        })
        bearer_token_response.raise_for_status()
        self.auth = bearer_token_response.json()["access_token"]

    def __get_auth(self):
        return self.auth  # just for refactoring later

    def get_kb_ids(self) -> [(str, str)]:
        kb_response = requests.get(f"{self.api_url}/knowledge-bases",
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

    def get_kb_documents_with_errors(self, kb_id: str) -> [(str, str)]:
        response = requests.get(f"{self.api_url}/knowledge-bases/{kb_id}/documents?offset=0&limit=500&sort_by=status&sort_direction=ASC",
                                headers={"Authorization": f"Bearer {self.__get_auth()}"})
        response.raise_for_status()
        error_docs = []
        for data in response.json()["elements"]:
            if data["status"] == "failed":
                error_docs.append((data["id"], data["status_message"]))
        return error_docs

    def delete_kb_document(self, kb_id: str, doc_id):
        response = requests.delete(f"{self.api_url}/knowledge-bases/{kb_id}/documents/{doc_id}",
                                   headers={"Authorization": f"Bearer {self.__get_auth()}"})
        response.raise_for_status()