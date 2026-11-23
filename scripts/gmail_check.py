from app.gmail import Gmail, get_body, get_headers

gmail = Gmail()
print("Connected as", gmail.address, "\n")

message_id = gmail.list_new_message_ids()[0]
print(message_id, "\n")
message = gmail.get_message(message_id)
print(message, "\n")
headers = get_headers(message)
print(headers["from"], "|", headers.get("subject"), "\n")
print(get_body(message)[:500], "\n")

gmail.send_reply(message, "Thanks, we received your email.")
print("Reply sent")