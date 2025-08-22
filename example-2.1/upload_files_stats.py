from UploadFiles import UploadFiles

FILENAME = "upload_files.json"
PRETTY_PRINT = False


def main():
    upload_files = UploadFiles()
    upload_files.from_file(FILENAME)

    total = 0
    allowed = {}
    not_allowed = {}
    for upload_file in upload_files.get_all_update_files():
        total += 1
        if upload_file.allowed:
            try:
                allowed[upload_file.status] += 1
            except KeyError:
                allowed.update({upload_file.status: 1})
        else:
            try:
                sub_dict = not_allowed[upload_file.status]
                try:
                    sub_dict[upload_file.file_type] += 1
                except KeyError:
                    sub_dict.update({upload_file.file_type: 1})
            except KeyError:
                not_allowed.update({upload_file.status: {upload_file.file_type: 1}})

    print(f"total files: {total}")
    print(f"\nallowed:")
    print(f"  total: {sum(allowed.values())}")
    for key, value in allowed.items():
        print(f"  {key}: {value}")

    print(f"\nnot allowed")
    print(f"  total: {total - sum(allowed.values())}")
    for status, doc_counts in not_allowed.items():
        print(f"  {status}: {sum(doc_counts.values())}")
        for doc_type, doc_count in doc_counts.items():
            print(f"    {doc_type}: {doc_count}")

    if PRETTY_PRINT:
        upload_files.to_file(FILENAME, True)


if __name__ == "__main__":
    main()
