import datetime
import time
import MyGPTAPI
import logging

api_config = MyGPTAPI.APIConfig()
api_config.from_file("api_config.json")
KB_NAME = "KB Name"
REPEATS = 60 * 12
REPEAT_INTERVALL = 60
LOOKBACK_TIME = datetime.timedelta(minutes=5)
BATCH_SIZE = 42


def main():
    api = MyGPTAPI.MyGPTAPI(api_config=api_config)
    kb_id = api.get_kb_id_by_name(KB_NAME)
    if kb_id is None:
        logging.error("kb name not found")
        exit(-1)

    for i in range(REPEATS):
        latest_documents, doc_count = api.get_latest_changed_kb_documents(kb_id=kb_id, duration=LOOKBACK_TIME,
                                                                          batch_size=BATCH_SIZE)
        states = {
            "failed": 0,
            "in_progress": 0,
            "queued": 0,
            "success": 0
        }
        for data in latest_documents: states[data["status"]] += 1
        str_states = [f"{status}:{str(count).rjust(3)}   " for status, count in states.items()]
        logging_str = ""
        for str_state in sorted(str_states): logging_str += str_state
        logging.info(logging_str)
        if REPEATS > 1:
            time.sleep(REPEAT_INTERVALL)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(name)-15s [%(levelname)-8s] %(message)s',
                        datefmt='%d.%m.%Y %H:%M:%S',
                        handlers=[
                            logging.FileHandler(__file__ + ".log"),
                            logging.StreamHandler()
                        ])
    main()
