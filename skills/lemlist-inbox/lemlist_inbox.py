"""Lemlist Inbox API client — dependency-free (stdlib urllib only).

Covers the unified inbox: reading conversations, drafts, labels, and sending /
replying on email, LinkedIn and WhatsApp.

Auth is HTTP Basic with an EMPTY username and the API key as the password.

    from lemlist_inbox import LemlistInbox
    lem = LemlistInbox()                     # LEMLIST_API_KEY via gtm.cred
    msgs = lem.get_contact_messages("ctc_...")

SENDING IS GUARDED. `send_email` / `send_linkedin` / `send_whatsapp` raise
unless the client was built with allow_send=True or $LEMLIST_ALLOW_SEND=1.
Sending puts a message in a real prospect's inbox: only do it after the user
explicitly says go for that message. Drafts are the default. See SKILL.md.
"""
from __future__ import annotations

import base64
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional

API_BASE = "https://api.lemlist.com/api"
HERE = os.path.dirname(os.path.abspath(__file__))


def _resolve_key() -> str:
    """LEMLIST_API_KEY via gtm.cred: environment, ~/.magna-gtm-config, api_keys table."""
    key = os.environ.get("LEMLIST_API_KEY", "").strip()
    if key:
        return key
    repo = os.path.abspath(os.path.join(HERE, "..", ".."))
    if os.path.exists(os.path.join(repo, "gtm.py")):
        import sys
        sys.path.insert(0, repo)
        import gtm  # noqa: E402
        key = (gtm.cred("LEMLIST_API_KEY", required=False) or "").strip()
    return key

# Rate limit is 20 requests / 2 seconds. 0.12s between calls keeps us under it.
_MIN_INTERVAL = 0.12
_last_call = [0.0]


class LemlistError(RuntimeError):
    """Lemlist returned a non-2xx. `status` is the HTTP code, `body` the raw text.

    Note Lemlist returns 400s as text/plain, not JSON.
    """

    def __init__(self, status: int, body: str):
        self.status = status
        self.body = body
        super().__init__(f"Lemlist API {status}: {body[:400]}")


class SendBlocked(RuntimeError):
    """Raised when a send is attempted without explicit opt-in."""


class LemlistInbox:
    def __init__(
        self,
        api_key: Optional[str] = None,
        allow_send: Optional[bool] = None,
        timeout: int = 30,
    ):
        self.api_key = (api_key or _resolve_key()).strip()
        if not self.api_key:
            raise ValueError("No Lemlist API key (LEMLIST_API_KEY). "
                             "Add it with: python3 gtm.py set-key LEMLIST_API_KEY")
        if allow_send is None:
            allow_send = os.environ.get("LEMLIST_ALLOW_SEND", "") == "1"
        self.allow_send = allow_send
        self.timeout = timeout

    # ---------------------------------------------------------------- transport

    def _request(self, method: str, path: str, params: dict = None, body: dict = None) -> Any:
        url = f"{API_BASE}{path}"
        if params:
            clean = {k: v for k, v in params.items() if v is not None}
            if clean:
                url += "?" + urllib.parse.urlencode(clean)

        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)

        token = base64.b64encode(f":{self.api_key}".encode()).decode()
        req.add_header("Authorization", f"Basic {token}")
        req.add_header("Accept", "application/json")
        # Lemlist sits behind Cloudflare, which bans urllib's default User-Agent
        # ("Python-urllib/3.x") with a 1010 browser_signature_banned. Any normal
        # UA passes. Without this every call 403s.
        req.add_header("User-Agent", "lemlist-inbox-client/1.0")
        if data:
            req.add_header("Content-Type", "application/json")

        # crude global throttle so callers can loop without tripping 429s
        elapsed = time.time() - _last_call[0]
        if elapsed < _MIN_INTERVAL:
            time.sleep(_MIN_INTERVAL - elapsed)
        _last_call[0] = time.time()

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode()
        except urllib.error.HTTPError as e:
            raw = e.read().decode(errors="replace")
            if e.code == 429:
                retry = int(e.headers.get("Retry-After", 2))
                time.sleep(retry)
                return self._request(method, path, params, body)
            raise LemlistError(e.code, raw) from None

        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw

    # ------------------------------------------------------------------ reading

    def get_conversations(self, limit: int = 50, skip: int = 0) -> Any:
        """GET /inbox — all team inbox conversations."""
        return self._request("GET", "/inbox", {"limit": limit, "skip": skip})

    def get_contact_messages(
        self,
        contact_id: str,
        limit: int = 20,
        skip: int = 0,
        user_id: str = None,
        mark_as_read: bool = False,
    ) -> Any:
        """GET /inbox/{contactId} — full message history with one contact.

        mark_as_read=True is a WRITE (clears the unread badge in the Lemlist
        inbox UI). Left off by default.
        """
        return self._request(
            "GET",
            f"/inbox/{contact_id}",
            {
                "limit": limit,
                "skip": skip,
                "userId": user_id,
                "markAsRead": "true" if mark_as_read else None,
            },
        )

    def get_thread_messages(self, contact_id: str, limit: int = 20) -> list:
        """Convenience: just the InboxMessage list, oldest first."""
        resp = self.get_contact_messages(contact_id, limit=limit)
        items = resp.get("data", []) if isinstance(resp, dict) else (resp or [])
        return sorted(items, key=lambda m: m.get("createdAt", ""))

    def latest_sender_triple(self, contact_id: str) -> Optional[dict]:
        """Pull sendUserId/Email/MailboxId off the most recent message in a thread.

        Use this when you need to reply but don't have a webhook payload to
        copy the sender from. Returns None if the thread is empty.
        """
        msgs = self.get_thread_messages(contact_id, limit=20)
        for m in reversed(msgs):
            if m.get("sendUserId") and m.get("sendUserMailboxId"):
                return {
                    "send_user_id": m["sendUserId"],
                    "send_user_email": m.get("sendUserEmail", ""),
                    "send_user_mailbox_id": m["sendUserMailboxId"],
                }
        return None

    # ------------------------------------------------------------------ sending

    def _check_send(self, what: str):
        if not self.allow_send:
            raise SendBlocked(
                f"{what} blocked. Sending reaches a real prospect. Pass allow_send=True "
                "or set LEMLIST_ALLOW_SEND=1 only after the user explicitly says go for "
                "this message. Use create_draft() otherwise."
            )

    def send_email(
        self,
        send_user_id: str,
        send_user_email: str,
        send_user_mailbox_id: str,
        message: str,
        contact_id: str = None,
        lead_id: str = None,
        subject: str = None,
        cc: list = None,
        reply_to_activity_id: str = None,
    ) -> dict:
        """POST /inbox/email — 🚨 sends a real email.

        message is HTML. On a reply, OMIT subject (the thread's is reused) and
        pass reply_to_activity_id ("latest" or an act_... id).
        """
        self._check_send("send_email")
        if not (contact_id or lead_id):
            raise ValueError("contact_id or lead_id is required")

        body = {
            "sendUserId": send_user_id,
            "sendUserEmail": send_user_email,
            "sendUserMailboxId": send_user_mailbox_id,
            "message": message,
        }
        if contact_id:
            body["contactId"] = contact_id
        if lead_id:
            body["leadId"] = lead_id
        if subject:
            body["subject"] = subject
        if cc is not None:
            body["cc"] = cc
        if reply_to_activity_id:
            body["replyToActivityId"] = reply_to_activity_id

        return self._request("POST", "/inbox/email", body=body)

    def reply_to_thread(
        self,
        sender: dict,
        contact_id: str,
        message_html: str,
        activity_id: str = "latest",
    ) -> dict:
        """Ergonomic wrapper: reply in-thread using a sender triple dict.

        `sender` accepts either snake_case (from latest_sender_triple) or the
        raw camelCase keys straight off a webhook payload.
        """
        return self.send_email(
            send_user_id=sender.get("send_user_id") or sender["sendUserId"],
            send_user_email=sender.get("send_user_email") or sender.get("sendUserEmail", ""),
            send_user_mailbox_id=sender.get("send_user_mailbox_id") or sender["sendUserMailboxId"],
            contact_id=contact_id,
            message=message_html,
            reply_to_activity_id=activity_id,
        )

    def send_linkedin(
        self,
        send_user_id: str,
        message: str,
        contact_id: str = None,
        lead_id: str = None,
    ) -> dict:
        """POST /inbox/linkedin — 🚨 sends a real LinkedIn message."""
        self._check_send("send_linkedin")
        body = {"sendUserId": send_user_id, "message": message}
        if contact_id:
            body["contactId"] = contact_id
        if lead_id:
            body["leadId"] = lead_id
        return self._request("POST", "/inbox/linkedin", body=body)

    def send_whatsapp(
        self,
        send_user_id: str,
        message: str,
        contact_id: str = None,
        lead_id: str = None,
    ) -> dict:
        """POST /inbox/whatsapp — 🚨 sends a real WhatsApp message."""
        self._check_send("send_whatsapp")
        body = {"sendUserId": send_user_id, "message": message}
        if contact_id:
            body["contactId"] = contact_id
        if lead_id:
            body["leadId"] = lead_id
        return self._request("POST", "/inbox/whatsapp", body=body)

    # ------------------------------------------------------------------- drafts

    def create_draft(
        self,
        contact_id: str,
        draft_owner: str,
        content: str,
        channel: str = "email",
        subject: str = None,
    ) -> dict:
        """POST /inbox/{contactId}/drafts — writes a draft into the Lemlist UI.

        The SAFE alternative to send_email: a human still hits Send.
        draft_owner is a usr_... id or a login email. Max 10 drafts per
        conversation; content max 30KB.
        """
        if len(content) > 30_000:
            raise ValueError("draft content exceeds the 30KB Lemlist limit")
        if channel not in ("email", "linkedin", "whatsapp", "sms"):
            raise ValueError(f"invalid channel: {channel}")
        body = {"content": content, "channel": channel}
        if subject:
            body["subject"] = subject
        return self._request(
            "POST", f"/inbox/{contact_id}/drafts", {"draftOwner": draft_owner}, body
        )

    def list_drafts(self, contact_id: str) -> Any:
        return self._request("GET", f"/inbox/{contact_id}/drafts")

    def get_draft(self, contact_id: str, draft_id: str) -> Any:
        return self._request("GET", f"/inbox/{contact_id}/drafts/{draft_id}")

    def update_draft(self, contact_id: str, draft_id: str, **fields) -> Any:
        return self._request("PATCH", f"/inbox/{contact_id}/drafts/{draft_id}", body=fields)

    def delete_draft(self, contact_id: str, draft_id: str) -> Any:
        return self._request("DELETE", f"/inbox/{contact_id}/drafts/{draft_id}")

    # ------------------------------------------------------------------- labels

    def list_labels(self) -> Any:
        return self._request("GET", "/inbox/labels")

    def create_label(self, name: str, color: str = None) -> Any:
        body = {"name": name}
        if color:
            body["color"] = color
        return self._request("POST", "/inbox/labels", body=body)

    def attach_labels(self, contact_id: str, label_ids: list) -> Any:
        return self._request(
            "POST", f"/inbox/conversations/labels/{contact_id}", body={"labelIds": label_ids}
        )

    def remove_labels(self, contact_id: str, label_ids: list) -> Any:
        return self._request(
            "DELETE", f"/inbox/conversations/labels/{contact_id}", body={"labelIds": label_ids}
        )

    # ----------------------------------------------------------------- webhooks

    def list_webhooks(self) -> Any:
        return self._request("GET", "/hooks")

    def add_webhook(
        self,
        target_url: str,
        event_type: str = None,
        campaign_id: str = None,
        is_first: bool = None,
    ) -> Any:
        """POST /hooks — register a callback.

        isFirst is read from the JSON BODY as a boolean; the documented query
        param is silently stored as null. is_first=True delivers only a lead's
        FIRST activity of that type, so a second reply from the same person
        never arrives. For replies prefer False and dedupe per message yourself.
        Lemlist allows one hook per targetUrl (a second one 409s, empty body).
        """
        body = {"targetUrl": target_url}
        if event_type:
            body["type"] = event_type
        if campaign_id:
            body["campaignId"] = campaign_id
        if is_first is not None:
            body["isFirst"] = bool(is_first)
        # campaignId also kept as a query param, the documented location.
        return self._request("POST", "/hooks", {"campaignId": campaign_id}, body)

    def delete_webhook(self, hook_id: str) -> Any:
        return self._request("DELETE", f"/hooks/{hook_id}")


# --------------------------------------------------------------------- helpers

# Matches the quoted-thread header Gmail/Outlook/Apple Mail prepend to a reply.
# NOTE: these headers routinely WRAP across lines ("On Mon, Nov 17 ... <a@b.com>\nwrote:")
# so the body patterns use [\s\S] rather than . and are not end-anchored.
_QUOTE_MARKERS = [
    re.compile(r"^\s*On [\s\S]{0,200}?\bwrote:", re.I | re.M),
    re.compile(r"^\s*Le [\s\S]{0,200}?\ba écrit\s*:", re.I | re.M),
    re.compile(r"^\s*El [\s\S]{0,200}?\bescribió:", re.I | re.M),
    re.compile(r"^\s*-{2,}\s*Original Message\s*-{2,}\s*$", re.I | re.M),
    re.compile(r"^\s*_{5,}\s*$", re.M),
    re.compile(r"^\s*From:\s.+$", re.M),
    re.compile(r"^\s*Sent from my \w+", re.I | re.M),
    # RFC 3676 signature delimiter ("-- " on its own line).
    re.compile(r"^\s*--\s*$", re.M),
]


def strip_quoted_reply(text: str) -> str:
    """Return only the NEW part of an email reply, dropping the quoted thread.

    Lemlist's webhook `text` field contains the reply followed by the entire
    quoted history. Feeding that to an LLM makes it answer the wrong message.
    """
    if not text:
        return ""

    cut = len(text)
    for pat in _QUOTE_MARKERS:
        m = pat.search(text)
        if m and m.start() < cut:
            cut = m.start()

    body = text[:cut]

    # Also drop any trailing run of ">" quoted lines the markers missed.
    lines = body.split("\n")
    while lines and (lines[-1].strip().startswith(">") or not lines[-1].strip()):
        lines.pop()

    return "\n".join(lines).strip()


def text_to_html(text: str) -> str:
    """Plain text -> the HTML Lemlist's `message` field expects.

    Newlines do not survive as-is; each paragraph becomes a <p>.
    """
    if not text:
        return ""
    escaped = (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )
    paras = [p.strip() for p in re.split(r"\n\s*\n", escaped) if p.strip()]
    return "".join(f"<p>{p.replace(chr(10), '<br>')}</p>" for p in paras)


def strip_html(html: str) -> str:
    """Crude HTML -> text, for showing a message body in logs or a terminal."""
    if not html:
        return ""
    txt = re.sub(r"<(script|style)[\s\S]*?</\1>", "", html, flags=re.I)
    txt = re.sub(r"<br\s*/?>", "\n", txt, flags=re.I)
    txt = re.sub(r"</?(p|div|tr|li|h[1-6]|blockquote)[^>]*>", "\n", txt, flags=re.I)
    txt = re.sub(r"<[^>]+>", "", txt)
    txt = (
        txt.replace("&nbsp;", " ").replace("&amp;", "&")
        .replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
        .replace("&#39;", "'")
    )
    return re.sub(r"\n{3,}", "\n\n", txt).strip()


def parse_webhook(payload: Any) -> dict:
    """Normalize a Lemlist webhook payload into a flat dict.

    Handles the two shapes seen in the wild: a bare object (direct Lemlist
    webhook) and a single-element array (routed via Zapier, Clay or another relay).
    """
    if isinstance(payload, list):
        payload = payload[0] if payload else {}
    if not isinstance(payload, dict):
        return {}

    # Some relays nest the real event under "body" or "data".
    for key in ("body", "data", "payload"):
        inner = payload.get(key)
        if isinstance(inner, dict) and inner.get("type"):
            payload = inner
            break
        if isinstance(inner, list) and inner and isinstance(inner[0], dict):
            payload = inner[0]
            break

    raw_text = payload.get("text", "") or strip_html(payload.get("html", ""))

    return {
        "activity_id": payload.get("_id", ""),
        "event_type": payload.get("type", ""),
        "contact_id": payload.get("contactId", ""),
        "lead_id": payload.get("leadId", ""),
        "lead_email": payload.get("leadEmail") or payload.get("email") or payload.get("fromEmail", ""),
        "subject": payload.get("subject", ""),
        "reply_text": strip_quoted_reply(raw_text),
        "reply_text_full": raw_text,
        "reply_html": payload.get("html", ""),
        "preview": payload.get("messagePreview", ""),
        "campaign_id": payload.get("campaignId", ""),
        "campaign_name": payload.get("campaignName", ""),
        "sequence_id": payload.get("sequenceId", ""),
        "sequence_step": payload.get("sequenceStep"),
        "is_first": payload.get("isFirst"),
        "is_bot": bool(payload.get("bot")),
        "stopped": payload.get("stopped"),
        "created_at": payload.get("createdAt", ""),
        "sender": {
            "send_user_id": payload.get("sendUserId", ""),
            "send_user_name": payload.get("sendUserName", ""),
            "send_user_email": payload.get("sendUserEmail", ""),
            "send_user_mailbox_id": payload.get("sendUserMailboxId", ""),
        },
        "raw": payload,
    }


if __name__ == "__main__":
    import sys

    cmds = {
        "conversations": lambda c, a: c.get_conversations(),
        "messages": lambda c, a: c.get_contact_messages(a[0]),
        "sender": lambda c, a: c.latest_sender_triple(a[0]),
        "drafts": lambda c, a: c.list_drafts(a[0]),
        "labels": lambda c, a: c.list_labels(),
        "webhooks": lambda c, a: c.list_webhooks(),
    }
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        print(f"usage: python3 lemlist_inbox.py <{'|'.join(cmds)}> [args]")
        sys.exit(1)
    client = LemlistInbox()
    print(json.dumps(cmds[sys.argv[1]](client, sys.argv[2:]), indent=2, default=str))
