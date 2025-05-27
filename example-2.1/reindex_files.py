import time

import MyGPTAPI
from dateutil import parser
import datetime
import pytz
import helpers

APICONFIG = MyGPTAPI.APIConfig()
APICONFIG.from_file("api_config.json")
KB_NAME = "kb name"
PAUSE = 120

OLDEST_DATE = datetime.datetime(1970,1,1)
NEWEST_DATE = datetime.datetime(2025, 5, 1)

def main():
    api = MyGPTAPI.MyGPTAPI(api_config=APICONFIG)
    kb_id = api.get_kb_id_by_name(KB_NAME)
    if kb_id is None:
        print("KB not found")
        exit(-1)

    docs = api.get_all_kb_documents(kb_id=kb_id)
    doc_ids = []
    utc = pytz.UTC
    localized_oldest = utc.localize(OLDEST_DATE)
    localized_newest = utc.localize(NEWEST_DATE)
    for doc in docs:
        if doc["status"] in ["in_progress", "queued"]:
            continue
        doc_change = parser.parse(doc["updated_at"])
        if localized_oldest <= doc_change <= localized_newest:
            doc_ids.append(doc["id"])

    if helpers.yes_no_question(f"about to reindex {len(doc_ids)} documents - continue?"):
        for i in range(0, len(doc_ids), 20):
            api.reindex_kb_documents(kb_id, doc_ids[i:i+20])
            print(f"started reindex for documents {str(doc_ids[i:i+20])}")
            time.sleep(PAUSE)


if __name__ == "__main__":
    main()
    print("Done")
