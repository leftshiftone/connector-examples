import MyGPTAPI
import helpers

APICONFIG = MyGPTAPI.APIConfig()
APICONFIG.from_file("api_config.json")
KB_NAME = "kb name"


def main():
    api = MyGPTAPI.MyGPTAPI(api_config=APICONFIG)
    kb_id = api.get_kb_id_by_name(KB_NAME)
    if kb_id is None:
        print("KB not found")
        exit(-1)

    errors = api.get_kb_documents_with_errors(kb_id)
    for error_short, docs in helpers.get_kb_documents_by_error(errors).items():
        if helpers.yes_no_question(f"{len(docs)} errors starting with '{error_short}' - reindex them?"):
            doc_ids = [doc["id"] for doc in docs]
            for i in range(0, len(docs), 20):
                api.reindex_kb_documents(kb_id, doc_ids[i:i+20])


if __name__ == "__main__":
    main()
    print("Done")
