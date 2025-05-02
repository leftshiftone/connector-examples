import MyGPTAPI

api_config = MyGPTAPI.APIConfig()
api_config.from_file("some_config.json")

api = MyGPTAPI.MyGPTAPI(api_config=api_config)
api.check_for_document_status(500)

