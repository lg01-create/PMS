Personal Management System (PMS)

A Windows-friendly, standalone personal management app built with Python + Flask + SQLite.
It keeps your data local by default and includes tasks, bookmarks, calendar (FullCalendar), notes, contacts, and a unified email view (Gmail + Outlook).

✨ Features

Dashboard

Quick view of tasks, events, and Bookmarks dashboard grouped by categories.

Tasks

Title, description, start/due dates (picker), priority, status.

Notes, links/files, subtasks, categories (work / personal / other), and tags.

Task title links to a details page with edit.

Bookmarks

Category-based dashboard (Daily use, Important, Personal, Company, Reference, Others).

Minimal title-only chips; sections can expand/collapse; each section scrolls (H & V).

Manage page with search, category filter, edit/delete.

Calendar

FullCalendar integration; create and view events.

Email

Multiple Gmail and Outlook (Microsoft 365) accounts.

Shows last N days (configurable), with deep links to open mails in the provider.

Notes & Contacts

Lightweight CRUD with timestamps.

Reminders (optional)

Background scheduler prints reminders for tasks coming due and upcoming events.

🧰 Tech Stack (minimal, local-first)

Python 3.11+ (Windows)

Flask, Jinja2, Flask-Login

SQLAlchemy + Flask-SQLAlchemy + SQLite

APScheduler (optional reminders)

FullCalendar (front-end calendar)

OAuth clients:

Gmail: google-api-python-client, google-auth-oauthlib

Outlook: msal (Microsoft Graph)

No cloud backend required. All data persists in data/app.db (SQLite).
