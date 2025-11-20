import asyncio
from typing import Dict, Optional
from instagrapi import Client
import httpx
import logging
from requests.exceptions import RetryError, HTTPError
from datetime import datetime
import secrets
from pathlib import Path
import mimetypes
import tempfile
import os
import random

class AccountManager:
    def __init__(self):
        self.clients: Dict[str, Client] = {}
        self._tokens: Dict[str, str] = {}
        self._options: Dict[str, Dict] = {}
        self._webhooks: Dict[str, list] = {}
        self._last_seen: Dict[tuple, str] = {}
        try:
            self.poll_interval = float(os.environ.get("POLL_INTERVAL", "1"))
            if self.poll_interval < 0.5:
                self.poll_interval = 0.5
        except Exception:
            self.poll_interval = 1.0

    def _k(self, username: str) -> str:
        return (username or "").strip().lower()

    def login(self, username: str, password: str, verification_code: Optional[str] = None, webhook_url: Optional[str] = None):
        c = Client()
        c.login(username, password, verification_code)
        logging.info(f"login_ok username={username}")
        key = self._k(username)
        self.clients[key] = c
        if key not in self._tokens:
            self._tokens[key] = secrets.token_hex(16)
        if webhook_url:
            self.add_webhook(key, webhook_url)
        return True

    def get_sessionid(self, username: str) -> Optional[str]:
        key = self._k(username)
        cli = self.clients.get(key)
        try:
            return getattr(cli, "sessionid", None)
        except Exception:
            return None

    def ensure_session(self, username: str, sessionid: str) -> bool:
        key = self._k(username)
        cli = self.clients.get(key)
        if cli and getattr(cli, "sessionid", None):
            return True
        c = Client()
        try:
            setattr(c, "sessionid", sessionid)
            self.clients[key] = c
            return True
        except Exception:
            return False

    def logout(self, username: str):
        key = self._k(username)
        if key in self.clients:
            try:
                self.clients[key].logout()
            except Exception:
                pass
            del self.clients[key]
        logging.info(f"logout_ok username={username}")
        return True

    def list_accounts(self):
        out = []
        for u in self.clients.keys():
            ws = list(self._webhooks.get(u, []))
            first = ws[0]["url"] if ws else None
            out.append({"username": u, "token": self._tokens.get(u), "webhooks": ws, "webhook_url": first})
        return out

    def send_message(self, username: str, recipient: str, text: str, overrides: Optional[dict] = None):
        key = self._k(username)
        if key not in self.clients:
            raise ValueError("account_not_logged")
        c = self.clients[key]
        user_id = None
        try:
            user_id = int(recipient)
        except Exception:
            user_id = c.user_id_from_username(recipient)
        logging.info(f"send_message_start username={username} recipient={recipient} user_id={user_id} text={text}")
        # pre-actions based on options
        opts = self.get_options(key)
        if overrides:
            opts = {**opts, **overrides}
        import time
        if opts.get("safe_mode", True):
            time.sleep(random.uniform(0.2, 0.6))
        if opts.get("delay_typing", True):
            total = random.uniform(1.0, 3.5)
            elapsed = 0.0
            step = 0.35
            while elapsed < total:
                time.sleep(step)
                elapsed += step
        if opts.get("mark_seen_previous", True):
            try:
                threads = c.direct_threads(amount=10, selected_filter="all")
                tid = None
                for t in threads:
                    participants = getattr(t, "users", [])
                    if any(getattr(u, "pk", None) == user_id for u in participants):
                        tid = t.id
                        break
                if tid:
                    try:
                        c.direct_thread_mark_seen(tid)
                    except Exception:
                        pass
            except Exception:
                pass
        if opts.get("view_profile", False):
            try:
                c.user_info(user_id)
                if opts.get("safe_mode", True):
                    time.sleep(random.uniform(0.2, 0.5))
            except Exception:
                pass
        if opts.get("view_stories", False):
            try:
                reels = c.user_reels(user_id)
                count = 0
                for m in reels or []:
                    try:
                        c.story_view(m.pk)
                    except Exception:
                        pass
                    count += 1
                    if opts.get("safe_mode", True):
                        time.sleep(random.uniform(0.2, 0.6))
                    if count >= 2:
                        break
            except Exception:
                pass
        c.direct_send(text, user_ids=[user_id])
        logging.info(f"send_message_sent username={username} user_id={user_id}")
        return True

    def resolve_user_id(self, username: str, handle: str) -> int:
        key = self._k(username)
        if key not in self.clients:
            raise ValueError("account_not_logged")
        c = self.clients[key]
        return c.user_id_from_username(handle)

    def send_file(self, username: str, recipient: str, source: str, overrides: Optional[dict] = None):
        key = self._k(username)
        if key not in self.clients:
            raise ValueError("account_not_logged")
        c = self.clients[key]
        try:
            user_id = int(recipient)
        except Exception:
            user_id = c.user_id_from_username(recipient)
        logging.info(f"send_file_start username={username} recipient={recipient} user_id={user_id} source={source}")
        opts = self.get_options(key)
        if overrides:
            opts = {**opts, **overrides}
        import time
        if opts.get("safe_mode", True):
            time.sleep(random.uniform(0.2, 0.6))
        if opts.get("delay_typing", True):
            total = random.uniform(1.0, 3.5)
            elapsed = 0.0
            step = 0.35
            while elapsed < total:
                time.sleep(step)
                elapsed += step
        if opts.get("mark_seen_previous", True):
            try:
                threads = c.direct_threads(amount=10, selected_filter="all")
                tid = None
                for t in threads:
                    participants = getattr(t, "users", [])
                    if any(getattr(u, "pk", None) == user_id for u in participants):
                        tid = t.id
                        break
                if tid:
                    try:
                        c.direct_thread_mark_seen(tid)
                    except Exception:
                        pass
            except Exception:
                pass
        if opts.get("view_profile", False):
            try:
                c.user_info(user_id)
                if opts.get("safe_mode", True):
                    time.sleep(random.uniform(0.2, 0.5))
            except Exception:
                pass
        if opts.get("view_stories", False):
            try:
                reels = c.user_reels(user_id)
                count = 0
                for m in reels or []:
                    try:
                        c.story_view(m.pk)
                    except Exception:
                        pass
                    count += 1
                    if opts.get("safe_mode", True):
                        time.sleep(random.uniform(0.2, 0.6))
                    if count >= 2:
                        break
            except Exception:
                pass
        tmp_created = False
        path = None
        if isinstance(source, str) and source.lower().startswith("http"):
            r = httpx.get(source, timeout=30)
            r.raise_for_status()
            ct = r.headers.get("content-type", "")
            ext = None
            if ct:
                ext = mimetypes.guess_extension(ct.split(";")[0].strip())
            if not ext:
                ext = os.path.splitext(source)[1]
            fd, tmp = tempfile.mkstemp(suffix=ext or "")
            os.close(fd)
            with open(tmp, "wb") as f:
                f.write(r.content)
            path = Path(tmp)
            tmp_created = True
        else:
            path = Path(source)
        ext = path.suffix.lower()
        try:
            if ext in (".jpg", ".jpeg", ".png", ".webp"):
                c.direct_send_photo(path, user_ids=[user_id], thread_ids=[])
            elif ext in (".mp4", ".mov", ".avi", ".mkv"):
                c.direct_send_video(path, user_ids=[user_id], thread_ids=[])
            else:
                c.direct_send_photo(path, user_ids=[user_id], thread_ids=[])
        finally:
            if tmp_created:
                try:
                    os.unlink(path)
                except Exception:
                    pass
        logging.info(f"send_file_sent username={username} user_id={user_id} source={str(path)}")
        return True

    async def poll_loop(self):
        while True:
            try:
                await asyncio.to_thread(self.poll_once)
            except Exception:
                logging.warning("poll_once_failed")
            await asyncio.sleep(self.poll_interval)

    def poll_once(self):
        for username, c in list(self.clients.items()):
            try:
                inbox = c.direct_threads(amount=20, selected_filter="unread", thread_message_limit=1)
            except Exception:
                logging.warning("direct_threads_failed")
                continue
            for thread in inbox:
                thread_id = thread.id
                last_msg = None
                try:
                    msgs = c.direct_messages(thread_id, amount=1)
                    last_msg = msgs[0] if msgs else None
                except (RetryError, HTTPError):
                    logging.warning("direct_messages_retry_or_http_error")
                    continue
                except Exception:
                    logging.warning("direct_messages_failed")
                    continue
                if not last_msg:
                    continue
                last_seen = self._last_seen.get((username, thread_id))
                if last_seen == getattr(last_msg, "id", None):
                    continue
                is_inbound = last_msg.user_id != c.user_id
                if not is_inbound:
                    self._last_seen[(username, thread_id)] = last_msg.id
                    continue
                ts = getattr(last_msg, "timestamp", None)
                if isinstance(ts, datetime):
                    ts = ts.isoformat()
                payload = {
                    "username": username,
                    "thread_id": thread_id,
                    "item_id": last_msg.id,
                    "sender_id": last_msg.user_id,
                    "text": getattr(last_msg, "text", None),
                    "timestamp": ts,
                }
                try:
                    sender_name = None
                    try:
                        info = c.user_info(last_msg.user_id)
                        sender_name = getattr(info, "username", None)
                    except Exception:
                        sender_name = None
                    logging.info(f"inbound_message username={username} sender_id={last_msg.user_id} sender={sender_name} thread_id={thread_id} text={getattr(last_msg, 'text', None)}")
                except Exception:
                    pass
                self.forward_to_webhook(username, payload)
                self._last_seen[(username, thread_id)] = last_msg.id

    def forward_to_webhook(self, username: str, payload: dict):
        hooks = self._webhooks.get(self._k(username), [])
        if not hooks:
            return
        for w in hooks:
            perms = w.get("permissions", {})
            pl = dict(payload)
            if not perms.get("text", True):
                pl.pop("text", None)
            try:
                r = httpx.post(w.get("url"), json=pl, timeout=10)
                logging.info(f"webhook_status username={username} wid={w.get('id')} code={r.status_code}")
            except Exception:
                logging.warning("webhook_post_failed")

    # token and options management (in-memory)
    def get_token(self, username: str) -> Optional[str]:
        return self._tokens.get(self._k(username))

    def set_token(self, username: str, token: str):
        self._tokens[self._k(username)] = token

    def get_options(self, username: str) -> Dict:
        return self._options.get(self._k(username)) or {"delay_typing": True, "mark_seen_previous": True, "view_profile": False, "view_stories": False, "safe_mode": True}

    def set_options(self, username: str, opts: Dict) -> Dict:
        cur = self.get_options(username)
        new = {**cur, **opts}
        self._options[self._k(username)] = new
        return new

    # webhooks (in-memory)
    def list_webhooks(self, username: str):
        return list(self._webhooks.get(self._k(username), []))

    def add_webhook(self, username: str, url: str, permissions: Optional[dict] = None):
        key = self._k(username)
        arr = self._webhooks.setdefault(key, [])
        wid = str(len(arr) + 1)
        arr.append({"id": wid, "url": url, "permissions": permissions or {"text": True}})
        return wid

    def update_webhook(self, username: str, wid: str, url: Optional[str] = None, permissions: Optional[dict] = None) -> bool:
        arr = self._webhooks.get(self._k(username), [])
        for w in arr:
            if w.get("id") == wid:
                if url is not None:
                    w["url"] = url
                if permissions is not None:
                    w["permissions"] = permissions
                return True
        return False

    def delete_webhook(self, username: str, wid: str) -> bool:
        arr = self._webhooks.get(self._k(username), [])
        idx = None
        for i, w in enumerate(arr):
            if w.get("id") == wid:
                idx = i
                break
        if idx is None:
            return False
        arr.pop(idx)
        return True

    def reset_account(self, username: str) -> bool:
        key = self._k(username)
        self._tokens.pop(key, None)
        self._webhooks.pop(key, None)
        self._options.pop(key, None)
        # clients remain logged; token regenerated on next call if needed
        return True