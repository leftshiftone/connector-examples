import time

import MyGPTAPI
import helpers

APICONFIG = MyGPTAPI.APIConfig()
APICONFIG.from_file("api_config.json")
KB_NAME = "kb name"
MAX_RETRIEVE_DOCS = 1000
MAX_REINDEX_DOCS = 1000

PAUSE = 30
REINDEX_BATCH_SIZE = 15
# only display errors with a min occurrence
MIN_DOCS_PER_ERROR = 10

# automatically reindex a certain count of errors
ALWAYS_REINDEX_AT_ERROR_COUNT = 9999

# run this more than once
INTERVALS = 1

def main():
    api = MyGPTAPI.MyGPTAPI(api_config=APICONFIG)
    kb_id = api.get_kb_id_by_name(KB_NAME)
    if kb_id is None:
        print("KB not found")
        exit(-1)

    for i in range(INTERVALS):
        reindex_docs = 0
        errors = api.get_kb_documents_with_errors(kb_id, max_docs=MAX_RETRIEVE_DOCS)
        reindex_doc_ids = []
        error_list = list(helpers.get_kb_documents_by_error(errors).items())
        error_list.sort(key=lambda x: len(x[1]), reverse=True)
        for error_short, docs in error_list:
            if len(docs) < MIN_DOCS_PER_ERROR:
                continue
            if len(docs) > ALWAYS_REINDEX_AT_ERROR_COUNT or helpers.yes_no_question(f"{len(docs)} errors starting with '{error_short}' - reindex them?"):
                reindex_doc_ids.extend([doc["id"] for doc in docs])
            if len(reindex_doc_ids) > MAX_REINDEX_DOCS:
                break
        reindex_doc_ids = reindex_doc_ids[:MAX_REINDEX_DOCS]

        for i in range(0, len(reindex_doc_ids), REINDEX_BATCH_SIZE):
            if i > 0:
                time.sleep(PAUSE)
            reindex_ids = reindex_doc_ids[i:i + REINDEX_BATCH_SIZE]
            api.reindex_kb_documents(kb_id, reindex_ids)
            print(f"started reindex for documents {str(reindex_ids)}")
            reindex_docs += len(reindex_ids)


if __name__ == "__main__":
    main()
    print("Done")
