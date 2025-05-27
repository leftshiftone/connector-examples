from typing import List, Dict
from threading import Event

def yes_no_question(question: str, stop_event: Event = None) -> bool:
    if stop_event is None:
        stop_event = Event()
    while not stop_event.is_set():
        answer = input(question + " (y/n)").lower().strip()
        if answer == "y":
            return True
        elif answer == "n":
            return False
        else:
            print("enter either y or n")
    return False


def get_kb_documents_by_error(kb_documents: List[dict]) -> Dict[str, List[dict]]:
    error_shorthands = {}
    for kb_document in kb_documents:
        short = kb_document["status_message"][:25]
        if short in error_shorthands.keys():
            error_shorthands[short].append(kb_document)
        else:
            error_shorthands.update({short: [kb_document]})
    return error_shorthands
