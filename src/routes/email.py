import os, json, pathlib, datetime, requests
from urllib.parse import urlparse, urljoin
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from flask_login import login_required
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import msal
from msal import SerializableTokenCache
from ..extensions import db
from ..models import GmailAccount, OutlookAccount

email_bp = Blueprint('email', __name__)

# --- Gmail ---
G_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def _g_client_secrets_path():
    return current_app.config.get('GOOGLE_CLIENT_SECRETS')

def _g_token_dir():
    return pathlib.Path(current_app.config.get('GOOGLE_TOKEN_DIR'))

def _g_token_path_for(email):
    safe = email.replace('@','_at_').replace('.','_')
    return _g_token_dir() / f"token_{safe}.json"

def _g_build_flow():
    secrets = _g_client_secrets_path()
    if not os.path.exists(secrets):
        return None, "Missing client secrets. Put your OAuth client file at: " + secrets
    redirect_uri = url_for('email.g_oauth2_callback', _external=True)
    flow = Flow.from_client_secrets_file(secrets, scopes=G_SCOPES, redirect_uri=redirect_uri)
    return flow, None

def _g_load_credentials(token_path: pathlib.Path) -> Credentials | None:
    if not token_path.exists():
        return None
    creds = Credentials.from_authorized_user_file(str(token_path), G_SCOPES)
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            token_path.write_text(creds.to_json())
        except Exception as ex:
            print("Credential refresh failed:", ex)
    return creds

# --- Outlook (Microsoft 365 via Graph) ---
O_SCOPES = ['openid', 'profile', 'offline_access', 'email', 'Mail.Read']

def _o_app_config_path():
    return current_app.config.get('OUTLOOK_APP_CONFIG')

def _o_token_dir():
    return pathlib.Path(current_app.config.get('OUTLOOK_TOKEN_DIR'))

def _o_token_path_for(email):
    safe = email.replace('@','_at_').replace('.','_')
    return _o_token_dir() / f"token_{safe}.bin"

def _o_load_app_and_cache(for_email: str | None = None):
    cfg_path = _o_app_config_path()
    if not os.path.exists(cfg_path):
        return None, None, "Missing Outlook app config. Create: " + cfg_path
    try:
        cfg = json.loads(pathlib.Path(cfg_path).read_text())
        client_id = cfg['client_id']
        client_secret = cfg['client_secret']
        tenant = cfg.get('tenant', 'common')
    except Exception as ex:
        return None, None, f"Invalid app_config.json: {ex}"
    authority = f"https://login.microsoftonline.com/{tenant}"
    cache = SerializableTokenCache()
    if for_email:
        tpath = _o_token_path_for(for_email)
        if tpath.exists():
            cache.deserialize(tpath.read_text())
    app = msal.ConfidentialClientApplication(
        client_id=client_id,
        client_credential=client_secret,
        authority=authority,
        token_cache=cache
    )
    return app, cache, None

def _o_save_cache(email: str, cache: SerializableTokenCache):
    if cache.has_state_changed:
        tpath = _o_token_path_for(email)
        tpath.parent.mkdir(parents=True, exist_ok=True)
        tpath.write_text(cache.serialize())

# --- Combined Inbox ---
@email_bp.route('/')
@login_required
def inbox():
    lookback_days = int(current_app.config.get('EMAIL_LOOKBACK_DAYS', 5))

    # Gmail accounts
    g_accounts = GmailAccount.query.order_by(GmailAccount.email.asc()).all()
    items = []
    for acc in g_accounts:
        token_path = pathlib.Path(acc.token_path)
        creds = _g_load_credentials(token_path)
        if not creds:
            continue
        try:
            service = build('gmail', 'v1', credentials=creds, cache_discovery=False)
            q = f"newer_than:{lookback_days}d -category:spam -in:trash"
            resp = service.users().messages().list(userId='me', q=q, maxResults=50).execute()
            msg_ids = [m['id'] for m in resp.get('messages', [])]
            for mid in msg_ids:
                m = service.users().messages().get(userId='me', id=mid, format='metadata',
                    metadataHeaders=['From','Subject','Date']).execute()
                headers = {h['name']: h['value'] for h in m.get('payload', {}).get('headers', [])}
                thread_id = m.get('threadId')
                items.append({
                    "provider": "gmail",
                    "account": acc.email,
                    "id": m['id'],
                    "threadId": thread_id,
                    "open_url": f"https://mail.google.com/mail/?authuser={acc.email}#all/{thread_id}",
                    "snippet": m.get('snippet',''),
                    "from": headers.get('From',''),
                    "subject": headers.get('Subject','(no subject)'),
                    "date": headers.get('Date','')
                })
        except Exception as ex:
            flash(f"Gmail fetch failed for {acc.email}: {ex}", "danger")

    # Outlook accounts
    o_accounts = OutlookAccount.query.order_by(OutlookAccount.email.asc()).all()
    for acc in o_accounts:
        app, cache, err = _o_load_app_and_cache(for_email=acc.email)
        if err:
            flash(err, "warning")
            continue
        try:
            # try silent token
            result = None
            accts = app.get_accounts(username=acc.email)
            if accts:
                result = app.acquire_token_silent(scopes=O_SCOPES, account=accts[0])
            if not result:
                flash(f"Outlook token expired for {acc.email}. Reconnect.", "warning")
                continue

            access_token = result['access_token']
            headers = {"Authorization": f"Bearer {access_token}"}

            since = (datetime.datetime.utcnow() - datetime.timedelta(days=lookback_days)).strftime("%Y-%m-%dT%H:%M:%SZ")
            url = ("https://graph.microsoft.com/v1.0/me/messages"
                   "?$select=subject,from,receivedDateTime,bodyPreview,webLink"
                   f"&$filter=receivedDateTime ge {since}"
                   "&$orderby=receivedDateTime desc&$top=50")
            resp = requests.get(url, headers=headers, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            for m in data.get('value', []):
                frm = (m.get('from', {}) or {}).get('emailAddress', {})
                items.append({
                    "provider": "outlook",
                    "account": acc.email,
                    "id": m.get('id'),
                    "threadId": m.get('conversationId'),
                    "open_url": m.get('webLink'),
                    "snippet": m.get('bodyPreview', ''),
                    "from": f"{frm.get('name','')} <{frm.get('address','')}>".strip(),
                    "subject": m.get('subject') or "(no subject)",
                    "date": m.get('receivedDateTime', '')
                })
        except Exception as ex:
            flash(f"Outlook fetch failed for {acc.email}: {ex}", "danger")

    # Sort all items by date
    def parse_date_generic(d):
        if not d:
            return datetime.datetime.min
        try:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(d)
        except Exception:
            try:
                return datetime.datetime.fromisoformat(d.replace('Z','+00:00'))
            except Exception:
                return datetime.datetime.min

    items.sort(key=lambda x: parse_date_generic(x['date']), reverse=True)
    return render_template('email/list.html', g_accounts=g_accounts, o_accounts=o_accounts, items=items, lookback_days=lookback_days)

# --- Gmail account management ---
@email_bp.route('/accounts')
@login_required
def accounts():
    secrets_missing = not os.path.exists(_g_client_secrets_path())
    g_accounts = GmailAccount.query.order_by(GmailAccount.email.asc()).all()
    o_cfg_missing = not os.path.exists(_o_app_config_path())
    o_accounts = OutlookAccount.query.order_by(OutlookAccount.email.asc()).all()
    return render_template('email/accounts.html',
        g_accounts=g_accounts,
        o_accounts=o_accounts,
        secrets_missing=secrets_missing,
        secrets_path=_g_client_secrets_path(),
        o_cfg_missing=o_cfg_missing,
        o_cfg_path=_o_app_config_path()
    )

@email_bp.route('/gmail/connect')
@login_required
def g_connect():
    flow, err = _g_build_flow()
    if err:
        flash(err, 'warning')
        return redirect(url_for('email.accounts'))
    auth_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true', prompt='consent')
    session['oauth_state'] = state
    return redirect(auth_url)

@email_bp.route('/oauth2/callback')
@login_required
def g_oauth2_callback():
    flow, err = _g_build_flow()
    if err:
        flash(err, 'warning')
        return redirect(url_for('email.accounts'))
    flow.fetch_token(authorization_response=request.url)
    creds = flow.credentials
    # Identify the account (email) via Gmail profile
    try:
        service = build('gmail', 'v1', credentials=creds, cache_discovery=False)
        profile = service.users().getProfile(userId='me').execute()
        email = profile.get('emailAddress')
    except Exception as ex:
        flash(f"Gmail: could not verify account: {ex}", "danger")
        return redirect(url_for('email.accounts'))
    # Save token
    token_path = _g_token_path_for(email)
    token_path.write_text(creds.to_json())
    # Upsert DB record
    acc = GmailAccount.query.filter_by(email=email).first()
    if not acc:
        acc = GmailAccount(email=email, token_path=str(token_path))
        db.session.add(acc)
    else:
        acc.token_path = str(token_path)
    db.session.commit()
    flash(f"Connected Gmail account: {email}", "success")
    return redirect(url_for('email.accounts'))

@email_bp.route('/gmail/<int:aid>/delete', methods=['POST'])
@login_required
def g_delete_account(aid):
    acc = GmailAccount.query.get_or_404(aid)
    try:
        pathlib.Path(acc.token_path).unlink(missing_ok=True)
    except Exception as ex:
        print("gmail token delete:", ex)
    db.session.delete(acc)
    db.session.commit()
    flash("Removed Gmail account", "info")
    return redirect(url_for('email.accounts'))

# --- Outlook account management ---
@email_bp.route('/outlook/connect')
@login_required
def o_connect():
    app, cache, err = _o_load_app_and_cache()
    if err:
        flash(err, 'warning')
        return redirect(url_for('email.accounts'))
    redirect_uri = url_for('email.o_oauth2_callback', _external=True)
    auth_url = app.get_authorization_request_url(scopes=O_SCOPES, redirect_uri=redirect_uri, prompt='consent')
    return redirect(auth_url)

@email_bp.route('/outlook/callback')
@login_required
def o_oauth2_callback():
    app, cache, err = _o_load_app_and_cache()
    if err:
        flash(err, 'warning')
        return redirect(url_for('email.accounts'))
    code = request.args.get('code')
    redirect_uri = url_for('email.o_oauth2_callback', _external=True)
    result = app.acquire_token_by_authorization_code(code, scopes=O_SCOPES, redirect_uri=redirect_uri)
    if 'access_token' not in result:
        flash(f"Outlook auth failed: {result.get('error_description')}", "danger")
        return redirect(url_for('email.accounts'))
    # Find email
    try:
        headers = {"Authorization": f"Bearer {result['access_token']}"}
        me = requests.get("https://graph.microsoft.com/v1.0/me?$select=mail,userPrincipalName", headers=headers, timeout=20).json()
        email = me.get('mail') or me.get('userPrincipalName')
    except Exception as ex:
        flash(f"Outlook: could not resolve account: {ex}", "danger")
        return redirect(url_for('email.accounts'))
    # Save cache to per-account file
    _o_save_cache(email, app.token_cache)
    # Upsert DB record
    acc = OutlookAccount.query.filter_by(email=email).first()
    if not acc:
        acc = OutlookAccount(email=email, token_path=str(_o_token_path_for(email)))
        db.session.add(acc)
    else:
        acc.token_path = str(_o_token_path_for(email))
    db.session.commit()
    flash(f"Connected Outlook account: {email}", "success")
    return redirect(url_for('email.accounts'))

@email_bp.route('/outlook/<int:aid>/delete', methods=['POST'])
@login_required
def o_delete_account(aid):
    acc = OutlookAccount.query.get_or_404(aid)
    try:
        pathlib.Path(acc.token_path).unlink(missing_ok=True)
    except Exception as ex:
        print("outlook token delete:", ex)
    db.session.delete(acc)
    db.session.commit()
    flash("Removed Outlook account", "info")
    return redirect(url_for('email.accounts'))
