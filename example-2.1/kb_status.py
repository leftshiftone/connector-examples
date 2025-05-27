import time
import MyGPTAPI
import logging

api_config = MyGPTAPI.APIConfig()
api_config.from_file("api_config.json")
KB_NAME = "KB Name"
REPEATS = 30
REPEAT_INTERVALL = 60*5


def main():
    api = MyGPTAPI.MyGPTAPI(api_config=api_config)
    for i in range(REPEATS):
        api.check_for_document_status(knowledgebase_name=KB_NAME)
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
