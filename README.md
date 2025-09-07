# Personal Management System (PMS)

A **Windows-friendly**, local-first personal management app built with **Python, Flask, and SQLite**.  
PMS keeps your data on your machine and brings together **Tasks, Bookmarks, Calendar (FullCalendar), Notes, Contacts, and Email (Gmail & Outlook)** in one place.

---

## Table of Contents
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Initial Setup (Windows)](#initial-setup-windows)
- [Running the App](#running-the-app)
- [Email Setup](#email-setup)
- [Configuration Reference](#configuration-reference)
- [Project Structure](#project-structure)
- [Admin: Create a User](#admin-create-a-user)
- [Troubleshooting](#troubleshooting)
- [Security Notes](#security-notes)
- [License](#license)
- [Roadmap](#roadmap)

---

## Features
- **Dashboard**
  - Quick summary of tasks & upcoming events.
  - **Bookmarks dashboard** grouped by: Daily use, Important, Personal, Company, Reference, Others (expand/collapse, scroll).
- **Tasks**
  - Description, notes, links/files, **subtasks**, categories (work/personal/other), **tags**.
  - Start date defaults to **today**; due date with a date picker.
  - Task title links to a **details** view with **edit**.
- **Bookmarks**
  - Clean **title-only** chips on the dashboard; each opens in a new tab.
  - **Manage** page with search, category filter, edit/delete.
- **Calendar**
  - FullCalendar view of events (create/view/navigate).
- **Email**
  - Connect **multiple Gmail and Microsoft 365/Outlook** accounts.
  - Shows last **N** days (configurable) with **deep links** to open in provider.
- **Notes & Contacts**
  - Lightweight CRUD with timestamps.
- **Reminders (optional)**
  - Background scheduler checks for due tasks and upcoming events and logs reminders.

---

## Architecture
- **Backend:** Flask + Flask-Login + SQLAlchemy (SQLite)
- **Frontend:** Jinja templates + FullCalendar + minimal JS/CSS
- **Storage:** Local SQLite DB (`data/app.db`) + per-provider token folders
- **Scheduler:** APScheduler (optional; can be disabled)

---

## Prerequisites
- **Python:** 3.11+ (3.12 works too)
- **Windows 10/11** (primary target). Linux/macOS work as well with minor path changes.
- (Optional, for HTTPS) **mkcert** or any dev TLS cert generator.

---

## Initial Setup (Windows)

Open **PowerShell** in the project folder (e.g., `C:\Projects\PMS`) and run:

```powershell
# 1) Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# 2) Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3) Copy default environment file and edit if needed
copy .env.example .env
# If you plan to test Gmail OAuth over HTTP during development:
#   set OAUTHLIB_INSECURE_TRANSPORT=1 in .env

# 4) One-time DB migration (adds missing columns like Bookmark.category)
python tools\ensure_bookmark_category.py
