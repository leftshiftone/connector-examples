from typing import List, Dict

def yes_no_question(question: str) -> bool:
    while True:
        answer = input(question + " (y/n)").lower().strip()
        if answer == "y":
            return True
        elif answer == "n":
            return False
        else:
            print("enter either y or n")


def get_kb_documents_by_error(kb_documents: List[dict]) -> Dict[str, List[dict]]:
    error_shorthands = {}
    for kb_document in kb_documents:
        short = kb_document["status_message"][:25]
        if short in error_shorthands.keys():
            error_shorthands[short].append(kb_document)
        else:
            error_shorthands.update({short: [kb_document]})
    return error_shorthands
