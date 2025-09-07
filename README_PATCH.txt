PMS v4 Email Patch — Gmail + Outlook + Configurable Lookback

This patch contains only the files you need to add:
  - Outlook (Office 365 / Microsoft Graph) support
  - Click-to-open links for emails
  - Configurable lookback days for both providers

HOW TO APPLY (Windows):
1) Extract this ZIP into your project root (same folder as app.py), letting it overwrite files.
2) Install new dependencies:
     .\.venv\Scripts\activate
     pip install -r requirements.txt
3) Gmail setup still uses data\gmail\client_secret.json.
4) Outlook setup:
     - Create Azure app (Web) in Azure Portal → App registrations.
     - Add Redirect URI:
         http(s)://127.0.0.1:5000/email/outlook/callback
     - API permissions (Delegated): Microsoft Graph → Mail.Read (and include offline_access)
     - Create a client secret.
     - Copy data\outlook\app_config.example.json → data\outlook\app_config.json
       and fill in client_id, client_secret, tenant (or 'common').
5) Set lookback days via .env:
     EMAIL_LOOKBACK_DAYS=5
   Restart the app. Email → Inbox header will show days.
6) Run:
     python app.py