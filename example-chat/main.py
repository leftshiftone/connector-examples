import json
from typing import Generator

import requests

# --------------------------------------------------------
# User/General settings
# --------------------------------------------------------
USER = "someuser@local"
PASSWORD = "???"
TENANT_ID = "a-tenant"
API_URL = "https://xyz.myg.pt/api/v1"


# --------------------------------------------------------
# Chat settings
# --------------------------------------------------------

#the channel to be used - if none this script prints all channels
# for the given user (copy the id and insert here)
CHANNEL_ID: str | None = None

# enables streaming mode see: streaming_chat/3 and chat/3
STREAMING=False

# --------------------------------------------------------
# business logic functions for clarity sake
# --------------------------------------------------------
def login() -> str:
    bearer_token_res = requests.post(f"{API_URL}/login", json={
        "email": USER,
        "password": PASSWORD,
        "tenant_id": TENANT_ID
    })
    bearer_token_res.raise_for_status()
    bearer_token = bearer_token_res.json()["access_token"]
    assert bearer_token is not None
    return bearer_token

def create_conversation(channel_id: str, bearer_token: str) -> str:
    """
    Creates a new conversation for a given channel
    see: https://api.myg.pt/api/v1/docs/redoc.html#tag/Conversations/operation/createConversation
    """
    create_conv_res = requests.post(f"{API_URL}/conversations",
    headers={
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    },
    json={
        "channel_id": channel_id,
        "description":"",
        "title":""
    })
    create_conv_res.raise_for_status()
    conv_id = create_conv_res.json()["id"]
    assert conv_id is not None
    return conv_id

def chat(message: str,
         conversation_id: str,
         bearer_token: str) -> str:
    """
    Demonstrates the usage of the conventional blocking message api
    see: https://api.myg.pt/api/v1/docs/redoc.html#tag/Messages/operation/createMessage
    """
    chat_res = requests.post(f"{API_URL}/messages",
                  headers={
                      "Authorization": f"Bearer {bearer_token}",
                      "Content-Type": "application/json",
                      "Accept": "application/json"
                  },
                  json={
                      "payload":message,
                      "origin":"user",
                      "channel_id":CHANNEL_ID,
                      "conversation_id": conversation_id
                  })
    chat_res.raise_for_status()
    chat_res_body = chat_res.json()
    assert chat_res_body["message"] is not None
    assert chat_res_body["message"]["payload"] is not None
    return chat_res_body["message"]["payload"]

def streaming_chat(message: str, conversation_id: str, bearer_token: str) ->Generator[dict]:
    """
    Demonstrates the message steaming api capabilities of MyGPT.
    The streaming API is implemented as a server-sent-events stream
    see: https://en.wikipedia.org/wiki/Server-sent_events
    see: https://api.myg.pt/api/v1/docs/redoc.html#tag/Messages/operation/createMessage
    """
    session = requests.Session()
    with session.post(f"{API_URL}/messages",
                             headers={
                                 "Authorization": f"Bearer {bearer_token}",
                                 "Content-Type": "application/json",
                                 "Accept": "text/event-stream"
                             },
                             json={
                                 "payload":message,
                                 "origin":"user",
                                 "channel_id":CHANNEL_ID,
                                 "conversation_id": conversation_id
                             }, stream=True) as response_stream:
        for line in response_stream.iter_lines():
            message = json.loads(line)
            yield message

def print_available_channels(bearer_token: str):
    """
    Prints the available channels for this user
    see: https://api.myg.pt/api/v1/docs/redoc.html#tag/Channels/operation/getChannelsForUser
    """
    available_channels_res = requests.get(url=f"{API_URL}/channels/own",
                                          headers={"Authorization": f"Bearer {bearer_token}"})
    print("Name\t|\t Channel Id")
    for channel in available_channels_res.json():
        print(f"{channel["name"]}\t|\t{channel["id"]}")


# --------------------------------------------------------
#  Actual main
# --------------------------------------------------------
def main():
    # 1. login and acquire the bearer token
    bearer_token = login()

    # 2. if no channel id is set print the available channels of this user
    # and exit (copy the id, set CHANNEL_ID and run the script again)
    if not CHANNEL_ID:
        print_available_channels(bearer_token)
        print("\n\nPlease set a channel id (see above)")
        return -1

    # 3. create a new conversation
    # note: you might use an already existing conversation as well
    # see: https://api.myg.pt/api/v1/docs/redoc.html#tag/Conversations/operation/getConversationsForUser
    conversation_id = create_conversation(CHANNEL_ID, bearer_token)

    # 4. chat away!
    if STREAMING:
        for m in streaming_chat("hi please write me a great lorem ipsum", conversation_id, bearer_token):
            print(m)
    else:
        answer = chat("hallo welt!", conversation_id, bearer_token)
        print(answer)

if __name__ == '__main__':
    main()