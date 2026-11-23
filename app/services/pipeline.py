import time
from email.utils import parseaddr

from pydantic_ai.exceptions import ModelUnavailableError

from app.clients import db
from app.ai.decide import decide
from app.clients.gmail import (
    ESCALATED_LABEL,
    PROCESSED_LABEL,
    Gmail,
    format_thread,
    get_body,
    get_headers,
    has_attachments,
)
from app.core.guards import skip_reason

MAX_ATTEMPTS = 1


def handle_message(gmail: Gmail, message_id: str) -> None:
    event = db.start_event(message_id)
    if event is None:
        gmail.add_label(message_id, PROCESSED_LABEL)
        return
    try:
        status, result = process(gmail, message_id)
        if status == "processed":
            gmail.add_label(message_id, PROCESSED_LABEL)
        db.finish_event(event["id"], status, result)
    except Exception as error:
        db.fail_event(event["id"], str(error))
        if event["attempts"] >= MAX_ATTEMPTS:
            gmail.add_label(message_id, PROCESSED_LABEL)
        raise


def process(gmail: Gmail, message_id: str) -> tuple[str, dict]:
    message = gmail.get_message(message_id)
    headers = get_headers(message)

    reason = skip_reason(message, headers, gmail.address)
    if reason:
        return "skipped", {"reason": reason}

    sender = parseaddr(headers.get("from", ""))[1]
    ticket_id = db.upsert_ticket(message["threadId"], sender, headers.get("subject", ""))
    db.save_message(ticket_id, message_id, "in", sender, get_body(message))

    thread = gmail.get_thread(message["threadId"])
    if gmail.is_escalated(thread):
        # A colleague owns this thread until they remove the needs-human label.
        return "skipped", {"reason": "thread is escalated"}

    ai_decision = None
    last_model_error = None
    for retry_attempt in range(MAX_ATTEMPTS):
        try:
            ai_decision = decide(format_thread(thread, gmail.address), has_attachments(message))
            break
        except ModelUnavailableError as model_error:
            last_model_error = model_error
            if retry_attempt < 2:
                time.sleep(2 ** retry_attempt)
    if ai_decision is None:
        # LLM unavailable after retries: leave ticket untouched (open / unlabeled)
        return "skipped", {"reason": "llm_unavailable", "error": str(last_model_error)}

    sent = gmail.send_reply(message, ai_decision.reply)
    db.save_message(ticket_id, sent["id"], "out", gmail.address, ai_decision.reply)
    if ai_decision.action == "escalate":
        gmail.add_label(message_id, ESCALATED_LABEL)
        db.update_ticket(ticket_id, "escalated", ai_decision.section, ai_decision.proposed_action)
    else:
        db.update_ticket(ticket_id, "answered", ai_decision.section)
    return "processed", ai_decision.model_dump()
