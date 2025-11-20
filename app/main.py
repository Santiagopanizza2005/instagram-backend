from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, HttpUrl
from typing import Optional
import asyncio
from .clients import AccountManager
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse
import httpx
import jwt
import time
from pathlib import Path
from fastapi import Header, Query
import tempfile
import os
import dotenv
dotenv.load_dotenv(override=True)
import secrets
import logging
from collections import deque

app = FastAPI()
manager = AccountManager()
BASE_PATH = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_PATH / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_PATH / "static")), name="static")
app.mount("/imagenes", StaticFiles(directory=str(BASE_PATH.parent / "imagenes"), check_dir=False), name="imagenes")

 

LOG_BUFFER = deque(maxlen=1000)
MONITOR_QUEUES: list[asyncio.Queue] = []

class MonitorHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
        except Exception:
            msg = str(record.getMessage())
        LOG_BUFFER.append(msg)
        for q in list(MONITOR_QUEUES):
            try:
                q.put_nowait(msg)
            except Exception:
                pass

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
handler = MonitorHandler()
handler.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logging.getLogger().setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
logging.getLogger().addHandler(handler)

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret")
JWT_EXPIRES = int(os.environ.get("JWT_EXPIRES", "86400"))
SUPABASE_URL = os.environ.get("SUPABASE_URL") or ""
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") or ""

CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "").strip()
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").strip()
try:
    MAX_UPLOAD_BYTES = int(os.environ.get("MAX_UPLOAD_BYTES", "3000000"))
except Exception:
    MAX_UPLOAD_BYTES = 3000000
origins = [o.strip() for o in CORS_ORIGINS.split(",") if o.strip()]
hosts = [h.strip() for h in ALLOWED_HOSTS.split(",") if h.strip()]
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
app.add_middleware(GZipMiddleware, minimum_size=1000)
if hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=hosts)

LOGIN_WINDOW_SECONDS = 60
LOGIN_MAX_ATTEMPTS = 8
LOGIN_ATTEMPTS: dict[str, deque] = {}

SB_TBL_USERS = "/app_users"
SB_TBL_ACCOUNTS = "/user_accounts"

def _sb_headers_service():
    return {"apikey": SUPABASE_SERVICE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"}

def _sb_rest(path: str):
    base = SUPABASE_URL.rstrip("/")
    return f"{base}/rest/v1{path}"

async def _sb_list_accounts(user_id: str):
    url = _sb_rest(SB_TBL_ACCOUNTS)
    params = {"select": "id,user_id,ig_username,ig_token,ig_sessionid,webhook_url,webhook_enabled,options,updated_at", "user_id": f"eq.{user_id}"}
    async with httpx.AsyncClient(timeout=15) as cli:
        r = await cli.get(url, headers=_sb_headers_service(), params=params)
        r.raise_for_status()
        return r.json()

async def _sb_get_account(user_id: str, ig_username: str):
    url = _sb_rest(SB_TBL_ACCOUNTS)
    params = {"select": "id,user_id,ig_username,ig_token,ig_sessionid,webhook_url,webhook_enabled,options,updated_at", "user_id": f"eq.{user_id}", "ig_username": f"eq.{ig_username}"}
    async with httpx.AsyncClient(timeout=15) as cli:
        r = await cli.get(url, headers=_sb_headers_service(), params=params)
        r.raise_for_status()
        rows = r.json()
        return rows[0] if rows else None

async def _sb_insert_account(user_id: str, ig_username: str):
    url = _sb_rest(SB_TBL_ACCOUNTS)
    payload = {"user_id": user_id, "ig_username": ig_username}
    async with httpx.AsyncClient(timeout=15) as cli:
        r = await cli.post(
            url,
            headers=_sb_headers_service() | {"Content-Type": "application/json", "Prefer": "return=representation"},
            json=payload,
        )
        r.raise_for_status()
        rows = r.json()
        return rows[0] if rows else None

async def _sb_update_account(user_id: str, ig_username: str, fields: dict):
    url = _sb_rest(SB_TBL_ACCOUNTS)
    params = {"user_id": f"eq.{user_id}", "ig_username": f"eq.{ig_username}"}
    async with httpx.AsyncClient(timeout=15) as cli:
        r = await cli.patch(url, headers=_sb_headers_service() | {"Content-Type": "application/json"}, params=params, json=fields)
        r.raise_for_status()
        return True

async def _ensure_owns_account(user_id: str, ig_username: str):
    acc = await _sb_get_account(user_id, ig_username)
    if not acc:
        raise HTTPException(status_code=403, detail="not_owner")
    return acc
async def _sb_update_user_refresh_token(user_id: str, refresh: str):
    url = _sb_rest(SB_TBL_USERS)
    params = {"id": f"eq.{user_id}"}
    async with httpx.AsyncClient(timeout=15) as cli:
        r = await cli.patch(url, headers=_sb_headers_service() | {"Content-Type": "application/json"}, params=params, json={"app_refresh_token": refresh})
        r.raise_for_status()
        return True

def _jwt_create(user_id: str):
    now = int(time.time())
    payload = {"sub": user_id, "iat": now, "exp": now + JWT_EXPIRES}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")
def _generate_refresh_token():
    return secrets.token_urlsafe(32)

def _jwt_verify(token: str):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except Exception:
        raise HTTPException(status_code=401, detail="invalid_session")

def _require_app_session(app_auth: str | None):
    if not app_auth or not app_auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing_session")
    tok = app_auth.split(" ", 1)[1]
    data = _jwt_verify(tok)
    return data.get("sub")

def _require_logged(username: str):
    key = (username or "").strip().lower()
    if key not in manager.clients:
        raise HTTPException(status_code=401, detail="account_not_logged")
    return True

def _require_auth(username: str, authorization: str | None):
    _require_logged(username)
    token = manager.get_token(username)
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing_auth")
    provided = authorization.split(" ", 1)[1]
    if provided != token:
        raise HTTPException(status_code=401, detail="invalid_token")
    return True

def _require_app_auth(app_auth: str | None):
    raise HTTPException(status_code=401, detail="app_auth_disabled")

class LoginBody(BaseModel):
    username: str
    password: str
    verification_code: Optional[str] = None
    webhook_url: Optional[HttpUrl] = None

class LogoutBody(BaseModel):
    username: str

class WebhookBody(BaseModel):
    webhook_url: HttpUrl | None = None
    enabled: Optional[bool] = None

class SendMessageBody(BaseModel):
    username: str
    recipient: str
    text: str

class ImportSessionBody(BaseModel):
    username: str
    sessionid: str
    csrftoken: Optional[str] = None
    ds_user_id: Optional[str] = None
    cookies: Optional[dict] = None
    webhook_url: Optional[HttpUrl] = None

class AppLoginBody(BaseModel):
    username: str
    password: str

def _rate_limit_check(key: str):
    now = int(time.time())
    q = LOGIN_ATTEMPTS.get(key)
    if q is None:
        q = deque()
        LOGIN_ATTEMPTS[key] = q
    while q and now - q[0] > LOGIN_WINDOW_SECONDS:
        q.popleft()
    if len(q) >= LOGIN_MAX_ATTEMPTS:
        raise HTTPException(status_code=429, detail="too_many_attempts")
    q.append(now)

@app.post("/api/login")
async def app_login(body: AppLoginBody, request: Request):
    ip = request.client.host if request and request.client else "unknown"
    _rate_limit_check(f"ip:{ip}")
    _rate_limit_check(f"user:{body.username}")
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise HTTPException(status_code=500, detail="supabase_not_configured")
    url = _sb_rest("/app_users")
    params = {"select": "id,username,password_hash,is_active", "username": f"eq.{body.username}"}
    async with httpx.AsyncClient(timeout=15) as cli:
        r = await cli.get(url, headers=_sb_headers_service(), params=params)
        r.raise_for_status()
        rows = r.json()
    if not rows:
        raise HTTPException(status_code=401, detail="invalid_credentials")
    row = rows[0]
    if not row.get("is_active", True):
        raise HTTPException(status_code=401, detail="inactive_user")
    import bcrypt
    try:
        ok = bcrypt.checkpw(body.password.encode("utf-8"), row["password_hash"].encode("utf-8"))
    except Exception:
        ok = False
    if not ok:
        raise HTTPException(status_code=401, detail="invalid_credentials")
    token = _jwt_create(row["id"])
    refresh = _generate_refresh_token()
    await _sb_update_user_refresh_token(row["id"], refresh)
    return {"ok": True, "token": token, "refresh": refresh, "user": {"id": row["id"], "username": row["username"]}}

@app.get("/api/verify-session")
def app_verify_session(app_auth: str | None = Header(None, alias="X-App-Session")):
    user_id = _require_app_session(app_auth)
    return {"ok": True, "user_id": user_id}

@app.post("/api/logout")
def app_logout():
    return {"ok": True}

@app.post("/api/refresh-session")
def app_refresh_session(app_auth: str | None = Header(None, alias="X-App-Session")):
    user_id = _require_app_session(app_auth)
    return {"ok": True, "token": _jwt_create(user_id)}
class RefreshBody(BaseModel):
    refresh: str

@app.post("/api/refresh-from-token")
async def app_refresh_from_token(body: RefreshBody):
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise HTTPException(status_code=500, detail="supabase_not_configured")
    url = _sb_rest(SB_TBL_USERS)
    params = {"select": "id,username,is_active,app_refresh_token", "app_refresh_token": f"eq.{body.refresh}"}
    async with httpx.AsyncClient(timeout=15) as cli:
        r = await cli.get(url, headers=_sb_headers_service(), params=params)
        r.raise_for_status()
        rows = r.json()
    if not rows:
        raise HTTPException(status_code=401, detail="invalid_refresh")
    row = rows[0]
    if not row.get("is_active", True):
        raise HTTPException(status_code=401, detail="inactive_user")
    token = _jwt_create(row["id"])
    return {"ok": True, "token": token}

@app.get("/")
def root():
    return {
        "ok": True,
        "name": "instagram-gateway",
        "docs_url": "/docs",
        "endpoints": [
            "/accounts/login",
            "/accounts/logout",
            "/accounts",
            "/accounts/{username}/webhook",
            "/accounts/{username}/token",
            "/accounts/{username}/token/reset",
            "/send_message",
            "/send_file",
            "/health",
        ],
    }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/ui", response_class=HTMLResponse)
def ui(request: Request):
    ver = secrets.token_hex(8)
    return templates.TemplateResponse("index.html", {"request": request, "version": ver})

 

@app.get("/monitor/logs")
def monitor_logs():
    return {"lines": list(LOG_BUFFER)}

@app.get("/monitor/stream")
async def monitor_stream():
    q: asyncio.Queue = asyncio.Queue()
    MONITOR_QUEUES.append(q)
    async def gen():
        for line in list(LOG_BUFFER):
            yield f"data: {line}\n\n"
        try:
            while True:
                line = await q.get()
                yield f"data: {line}\n\n"
        finally:
            try:
                MONITOR_QUEUES.remove(q)
            except Exception:
                pass
    headers = {"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"}
    return StreamingResponse(gen(), media_type="text/event-stream", headers=headers)

@app.on_event("startup")
async def on_startup():
    asyncio.create_task(manager.poll_loop())

 

@app.post("/user/signup")
def user_signup():
    raise HTTPException(status_code=410, detail="user_system_removed")

@app.post("/user/login")
def user_login():
    raise HTTPException(status_code=410, detail="user_system_removed")

@app.post("/user/logout")
def user_logout():
    raise HTTPException(status_code=410, detail="user_system_removed")

@app.post("/accounts/login")
async def login(body: LoginBody, app_auth: str | None = Header(None, alias="X-App-Session")):
    user_id = _require_app_session(app_auth)
    try:
        manager.login(body.username, body.password, body.verification_code, str(body.webhook_url) if body.webhook_url else None)
        acc = await _sb_get_account(user_id, body.username)
        if not acc:
            await _sb_insert_account(user_id, body.username)
        try:
            t = manager.get_token(body.username)
            if t:
                await _sb_update_account(user_id, body.username, {"ig_token": t})
        except Exception:
            pass
        try:
            sid = manager.get_sessionid(body.username)
            if sid:
                await _sb_update_account(user_id, body.username, {"ig_sessionid": sid})
        except Exception:
            pass
        if body.webhook_url:
            await _sb_update_account(user_id, body.username, {"webhook_url": str(body.webhook_url)})
            manager.add_webhook(body.username, str(body.webhook_url))
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/accounts/import-session")
async def import_session(body: ImportSessionBody, app_auth: str | None = Header(None, alias="X-App-Session")):
    user_id = _require_app_session(app_auth)
    if not body.username or not body.sessionid:
        raise HTTPException(status_code=400, detail="missing_fields")
    try:
        manager.import_session(body.username, body.sessionid, body.cookies or None, str(body.webhook_url) if body.webhook_url else None)
        acc = await _sb_get_account(user_id, body.username)
        if not acc:
            await _sb_insert_account(user_id, body.username)
        await _sb_update_account(user_id, body.username, {"ig_sessionid": body.sessionid})
        if body.webhook_url:
            await _sb_update_account(user_id, body.username, {"webhook_url": str(body.webhook_url)})
            manager.add_webhook(body.username, str(body.webhook_url))
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/accounts/logout")
async def logout(body: LogoutBody, app_auth: str | None = Header(None, alias="X-App-Session")):
    user_id = _require_app_session(app_auth)
    await _ensure_owns_account(user_id, body.username)
    manager.logout(body.username)
    return {"ok": True}

@app.get("/accounts")
async def accounts(app_auth: str | None = Header(None, alias="X-App-Session")):
    user_id = _require_app_session(app_auth)
    rows = await _sb_list_accounts(user_id)
    items = []
    for r in rows:
        try:
            u = r.get("ig_username")
            sid = r.get("ig_sessionid")
            if u and sid:
                manager.ensure_session(u, sid)
        except Exception:
            pass
        items.append({
            "username": r.get("ig_username"),
            "webhook_url": r.get("webhook_url"),
            "webhook_enabled": r.get("webhook_enabled", True),
        })
    return {"accounts": items}

@app.post("/accounts/{username}/webhook")
async def set_webhook(username: str, body: WebhookBody, authorization: str | None = Header(None), app_auth: str | None = Header(None, alias="X-App-Session")):
    user_id = _require_app_session(app_auth)
    _require_auth(username, authorization)
    await _ensure_owns_account(user_id, username)
    fields = {}
    if body.webhook_url:
        fields["webhook_url"] = str(body.webhook_url)
        if body.enabled is None:
            fields["webhook_enabled"] = True
    if body.enabled is not None:
        fields["webhook_enabled"] = body.enabled
    if fields:
        await _sb_update_account(user_id, username, fields)
    try:
        if body.enabled is False:
            manager._webhooks.pop(username, None)
        else:
            url = str(body.webhook_url) if body.webhook_url else None
            if not url:
                acc = await _sb_get_account(user_id, username)
                url = acc.get("webhook_url") if acc else None
            if url:
                manager._webhooks.pop(username, None)
                manager.add_webhook(username, url)
    except Exception:
        pass
    return {"ok": True}

@app.post("/accounts/{username}/reset")
def reset_account(username: str, authorization: str | None = Header(None), app_auth: str | None = Header(None, alias="X-App-Session")):
    _require_app_session(app_auth)
    _require_auth(username, authorization)
    manager.reset_account(username)
    return {"ok": True}

@app.get("/accounts/{username}/options")
async def get_options(username: str, authorization: str | None = Header(None), app_auth: str | None = Header(None, alias="X-App-Session")):
    user_id = _require_app_session(app_auth)
    _require_auth(username, authorization)
    acc = await _ensure_owns_account(user_id, username)
    opts = acc.get("options") or {}
    return {"options": opts}

class OptionsBody(BaseModel):
    delay_typing: Optional[bool] = None
    mark_seen_previous: Optional[bool] = None
    view_profile: Optional[bool] = None
    view_stories: Optional[bool] = None
    safe_mode: Optional[bool] = None

@app.post("/accounts/{username}/options")
async def set_options(username: str, body: OptionsBody, authorization: str | None = Header(None), app_auth: str | None = Header(None, alias="X-App-Session")):
    user_id = _require_app_session(app_auth)
    _require_auth(username, authorization)
    await _ensure_owns_account(user_id, username)
    opts = {k:v for k,v in body.model_dump().items() if v is not None}
    await _sb_update_account(user_id, username, {"options": opts})
    manager.set_options(username, opts)
    return {"options": opts}

@app.post("/send_message")
def send_message(
    body: SendMessageBody,
    authorization: str | None = Header(None),
    typing: bool | None = Query(None),
    seen: bool | None = Query(None),
    profile: bool | None = Query(None),
    stories: bool | None = Query(None),
    safe: bool | None = Query(None),
):
    try:
        _require_auth(body.username, authorization)
        overrides = {}
        if typing is not None:
            overrides["delay_typing"] = typing
        if seen is not None:
            overrides["mark_seen_previous"] = seen
        if profile is not None:
            overrides["view_profile"] = profile
        if stories is not None:
            overrides["view_stories"] = stories
        if safe is not None:
            overrides["safe_mode"] = safe
        manager.send_message(body.username, body.recipient, body.text, overrides if overrides else None)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/send_file")
async def send_file(
    request: Request,
    authorization: str | None = Header(None),
    typing: bool | None = Query(None),
    seen: bool | None = Query(None),
    profile: bool | None = Query(None),
    stories: bool | None = Query(None),
    safe: bool | None = Query(None),
):
    try:
        username = None
        recipient = None
        file_url = None
        upload = None
        ct = request.headers.get("content-type", "")
        if "multipart/form-data" in ct:
            form = await request.form()
            username = form.get("username")
            recipient = form.get("recipient")
            upload = form.get("file")
            file_url = form.get("file_url")
        else:
            body = await request.json()
            username = body.get("username")
            recipient = body.get("recipient")
            file_url = body.get("file_url")
        if not username or not recipient:
            raise HTTPException(status_code=400, detail="missing_fields")
        _require_auth(username, authorization)
        overrides = {}
        if typing is not None:
            overrides["delay_typing"] = typing
        if seen is not None:
            overrides["mark_seen_previous"] = seen
        if profile is not None:
            overrides["view_profile"] = profile
        if stories is not None:
            overrides["view_stories"] = stories
        if safe is not None:
            overrides["safe_mode"] = safe
        tmp_path = None
        if upload and hasattr(upload, "read"):
            fd, tmp = tempfile.mkstemp()
            os.close(fd)
            data = await upload.read()
            if MAX_UPLOAD_BYTES and isinstance(data, (bytes, bytearray)) and len(data) > MAX_UPLOAD_BYTES:
                raise HTTPException(status_code=413, detail="file_too_large")
            with open(tmp, "wb") as f:
                f.write(data)
            tmp_path = tmp
        source = file_url or tmp_path
        if not source:
            raise HTTPException(status_code=400, detail="file_required")
        manager.send_file(username, recipient, source, overrides if overrides else None)
        return {"ok": True}
    except Exception as e:
        code = 400
        if str(e) == "file_too_large":
            code = 413
        raise HTTPException(status_code=code, detail=str(e))

@app.get("/accounts/{username}/resolve/{handle}")
def resolve_user(username: str, handle: str, authorization: str | None = Header(None)):
    _require_auth(username, authorization)
    try:
        uid = manager.resolve_user_id(username, handle)
        return {"user_id": uid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/accounts/{username}/token")
async def get_token(username: str, app_auth: str | None = Header(None, alias="X-App-Session")):
    user_id = _require_app_session(app_auth)
    _require_logged(username)
    acc = await _ensure_owns_account(user_id, username)
    t = acc.get("ig_token")
    if not t:
        # fallback to manager
        t = manager.get_token(username)
    if not t:
        raise HTTPException(status_code=404, detail="token_missing")
    if manager.get_token(username) != t:
        manager.set_token(username, t)
    return {"token": t}

@app.post("/accounts/{username}/token/reset")
async def reset_token(username: str, authorization: str | None = Header(None), app_auth: str | None = Header(None, alias="X-App-Session")):
    user_id = _require_app_session(app_auth)
    _require_auth(username, authorization)
    await _ensure_owns_account(user_id, username)
    new = secrets.token_hex(16)
    manager.set_token(username, new)
    await _sb_update_account(user_id, username, {"ig_token": new})
    return {"token": new}

class WebhookCreateBody(BaseModel):
    url: HttpUrl
    permissions: Optional[dict] = None

class WebhookUpdateBody(BaseModel):
    url: Optional[HttpUrl] = None
    permissions: Optional[dict] = None

@app.get("/accounts/{username}/webhooks")
def list_webhooks(username: str, authorization: str | None = Header(None), app_auth: str | None = Header(None, alias="X-App-Session")):
    _require_app_session(app_auth)
    _require_auth(username, authorization)
    return {"webhooks": manager.list_webhooks(username)}

@app.post("/accounts/{username}/webhooks")
def add_webhook(username: str, body: WebhookCreateBody, authorization: str | None = Header(None), app_auth: str | None = Header(None, alias="X-App-Session")):
    _require_app_session(app_auth)
    _require_auth(username, authorization)
    wid = manager.add_webhook(username, str(body.url), body.permissions)
    return {"id": wid}

@app.put("/accounts/{username}/webhooks/{wid}")
def update_webhook(username: str, wid: str, body: WebhookUpdateBody, authorization: str | None = Header(None), app_auth: str | None = Header(None, alias="X-App-Session")):
    _require_app_session(app_auth)
    _require_auth(username, authorization)
    ok = manager.update_webhook(username, wid, str(body.url) if body.url else None, body.permissions)
    if not ok:
        raise HTTPException(status_code=404, detail="webhook_not_found")
    return {"ok": True}

@app.delete("/accounts/{username}/webhooks/{wid}")
def delete_webhook(username: str, wid: str, authorization: str | None = Header(None), app_auth: str | None = Header(None, alias="X-App-Session")):
    _require_app_session(app_auth)
    _require_auth(username, authorization)
    manager.delete_webhook(username, wid)
    return {"ok": True}

class TestWebhookBody(BaseModel):
    username: str
    text: str = "test"

@app.post("/test_webhook")
def test_webhook(body: TestWebhookBody, authorization: str | None = Header(None)):
    try:
        _require_auth(body.username, authorization)
        payload = {
            "username": body.username,
            "thread_id": "test",
            "item_id": "test",
            "sender_id": 0,
            "text": body.text,
            "timestamp": None,
        }
        manager.forward_to_webhook(body.username, payload)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/crm/{username}/threads")
def crm_threads(username: str, authorization: str | None = Header(None)):
    _require_auth(username, authorization)
    return {"threads": []}

@app.get("/crm/{username}/threads/{thread_id}")
def crm_thread(username: str, thread_id: str, authorization: str | None = Header(None)):
    _require_auth(username, authorization)
    return {"thread_id": thread_id, "messages": []}

class CRMReplyBody(BaseModel):
    text: str

@app.post("/crm/{username}/threads/{thread_id}/reply")
def crm_reply(
    username: str,
    thread_id: str,
    body: CRMReplyBody,
    authorization: str | None = Header(None),
    typing: bool | None = Query(None),
    seen: bool | None = Query(None),
    profile: bool | None = Query(None),
    stories: bool | None = Query(None),
    safe: bool | None = Query(None),
):
    try:
        _require_auth(username, authorization)
        rid = None
        try:
            rid = int(thread_id)
        except Exception:
            raise HTTPException(status_code=404, detail="contact_missing")
        overrides = {}
        if typing is not None:
            overrides["delay_typing"] = typing
        if seen is not None:
            overrides["mark_seen_previous"] = seen
        if profile is not None:
            overrides["view_profile"] = profile
        if stories is not None:
            overrides["view_stories"] = stories
        if safe is not None:
            overrides["safe_mode"] = safe
        manager.send_message(username, str(rid), body.text, overrides if overrides else None)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
@app.middleware("http")
async def _no_cache_static(request: Request, call_next):
    response = await call_next(request)
    p = request.url.path
    if p.startswith("/static") or p.startswith("/imagenes"):
        response.headers["Cache-Control"] = "no-store"
    return response

@app.middleware("http")
async def _limit_content_length(request: Request, call_next):
    cl = request.headers.get("content-length")
    try:
        if cl and MAX_UPLOAD_BYTES and int(cl) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="payload_too_large")
    except Exception:
        pass
    return await call_next(request)

@app.middleware("http")
async def _security_headers(request: Request, call_next):
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "no-referrer"
    return resp

@app.get("/db/health")
def db_health():
    try:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            return {"ok": False, "sb_ok": False, "error": "supabase_not_configured"}
        url = _sb_rest(SB_TBL_USERS)
        params = {"select": "id", "limit": 1}
        import anyio
        async def check():
            async with httpx.AsyncClient(timeout=10) as cli:
                r = await cli.get(url, headers=_sb_headers_service(), params=params)
                r.raise_for_status()
                return True
        ok = anyio.run(check)
        return {"ok": True, "sb_ok": ok, "url": SUPABASE_URL}
    except Exception as e:
        return {"ok": False, "sb_ok": False, "error": str(e), "url": SUPABASE_URL}
