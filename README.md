# 🚀 TIC Matrix Documentation Platform

<div align="center">

<img src="Documentation_Platform/static/TIC Matrix.png" alt="TIC Matrix Logo" width="150" height="150">

[![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.x-success?style=for-the-badge&logo=django)](https://www.djangoproject.com/)
[![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Google Drive API](https://img.shields.io/badge/Google_Drive_API-4285F4?style=for-the-badge&logo=googledrive&logoColor=white)](https://developers.google.com/drive)

**A secure, centralized, and role-based documentation repository for the TIC Matrix Club.**

*this project is under the tesing and further development*

</div>

## 📖 Overview

The TIC Matrix Documentation Platform is a customized enterprise-grade portal designed to securely store and manage the club's intellectual property. Built to eliminate information silos, it serves as a central hub for Bootcamp reports, Inter-Department Meetings (IDM), Official Department Meetings (ODM), Monthly Progress reports, and general guidelines. Integrating seamlessly with Google Drive for underlying storage, it enforces strict confidentiality through dynamic Role-Based Access Control (RBAC).

## ✨ Features

- 🔐 **Role-Based Access Control (RBAC)**: Custom authorization layers ensuring confidentiality. Roles include *President*, *Admin*, and *Head of Department*, dictating who can upload, view, modify, or delete specific departmental reports.
- ☁️ **Google Drive Integration**: Automated backend synchronization with Google Drive. Uploaded `.docx` files are automatically converted to Google Docs format for collaborative editing, with live PDF exports generated on the fly.
- 📂 **Structured Categorization**: Dedicated workspaces for IDM, ODM, Bootcamp, Monthly Progress, and Guidelines, keeping documents highly organized.
- 🛡️ **Advanced Security & OTP**: Features custom-built email OTP verification for secure password changes and credential resets, alongside Django's robust session security.
- 👁️ **Live Document Previews**: Integrated UI overlays allowing users to quickly preview Google Docs and PDFs directly within the platform without downloading.
- 🎨 **Modern UI/UX**: A clean, responsive, custom-styled interface featuring interactive cards, drag-and-drop file uploads, and animated components.

## 🛠️ Tech Stack

**Backend:**
- Python 3.x
- Django 5.x
- Google API Python Client (OAuth 2.0 & Service Accounts)

**Frontend:**
- HTML5 & CSS3 (Custom Responsive Styling)
- Vanilla JavaScript (for modals, previews, and AJAX form handling)
- Django Templates

**Database & Configuration:**
- MySQL
- `python-dotenv` for secure environment variable management

## 🚀 Quick Start

### Prerequisites
- Python 3.x installed
- MySQL Server installed and running
- Google Cloud Console account (with Google Drive API enabled and OAuth credentials generated)

### Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/infin8-innov8/Documentation_Paltform
    cd Documentation_Paltform/Documentation_Platform
    ```

2.  **Create and activate a virtual environment**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: .\venv\Scripts\activate
    ```

3.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Environment Setup**
    Create a `.env` file in the root directory alongside `settings.py` and configure the following:
    ```env
    DB_NAME=your_db_name
    DB_USER=your_db_user
    DB_PASSWORD=your_db_password
    DB_HOST=localhost
    DB_PORT=3306

    EMAIL_HOST_USER=your_club_email@gmail.com
    APP_PASSWORD=your_google_app_password
    ```

5.  **Google Drive Authentication Setup**
    Place your `client_secret.json` from the Google Cloud Console into the `doc_management` directory. Then, run the automated setup command to generate the OAuth token:
    ```bash
    python manage.py setup_gdrive
    ```

6.  **Database Initialization & Seeding**
    Apply migrations and populate the initial roles, permissions, departments, and users:
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    python manage.py setup_platform
    ```

7.  **Start the development server**
    ```bash
    python manage.py runserver
    ```
    Visit `http://localhost:8000` to access the platform.

## 📁 Project Structure

```text
Documentation_Platform/
├── auth_autho/                 # Authentication & RBAC management app
│   ├── management/commands/    # Custom setup scripts (setup_platform.py)
│   ├── migrations/             # Database schema migrations
│   ├── models.py               # Custom User, Role, Permission, Department models
│   └── views.py                # Login, Logout, OTP, Password Reset logic
├── doc_management/             # Core document storage app
│   ├── management/commands/    # Drive API setup (setup_gdrive.py)
│   ├── gdrive_service.py       # Google Drive API upload, conversion, and link generation
│   ├── models.py               # Report metadata models mapping to Drive IDs
│   └── views.py                # Dashboard routing and document upload/delete logic
├── Documentation_Platform/     # Django core configuration (settings.py, urls.py)
├── static/                     # Static assets (TIC Matrix logo, global CSS)
├── templates/                  # Django HTML templates (Dashboard, Forms, Modals)
├── .env                        # Environment variables (Database, Email SMTP)
└── manage.py                   # Django CLI utility
