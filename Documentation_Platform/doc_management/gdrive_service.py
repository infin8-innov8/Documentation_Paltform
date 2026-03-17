import os
import logging
from pathlib import Path
from io import BytesIO

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/drive']

BASE_DIR = Path(__file__).resolve().parent
CLIENT_SECRET_FILE = BASE_DIR / 'client_secret.json'
TOKEN_FILE = BASE_DIR / 'token.json'

# Folder names on Google Drive
ROOT_FOLDER_NAME = 'TIC_Doc_Platform'
SUBFOLDER_MAP = {
    'IDM': 'IDM_Reports',
    'ODM': 'ODM_Reports',
    'BOOTCAMP': 'Bootcamp_Reports',
}


SERVICE_ACCOUNT_FILE = BASE_DIR / 'service_account.json'

def _get_credentials():
    """
    Get or refresh Google Drive credentials.
    Priority:
    1. token.json (Saved from one-time setup) - Represents a manual admin authorization
    2. service_account.json (Cleanest for server-side, but has limited storage)
    3. client_secret.json (Fails if token is missing to prevent hanging)
    """
    from google.oauth2 import service_account
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    # 1. Try stored OAuth token (Option B - Admin's personal account)
    creds = None
    if TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
            if creds and creds.valid:
                return creds
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                return creds
        except Exception as e:
            logger.error(f"Error loading/refreshing token: {e}")

    # 2. Try Service Account (Option A - Dedicated account)
    if SERVICE_ACCOUNT_FILE.exists():
        try:
            return service_account.Credentials.from_service_account_file(
                str(SERVICE_ACCOUNT_FILE), scopes=SCOPES
            )
        except Exception as e:
            logger.error(f"Error loading service account: {e}")

    # 3. If no valid credentials, DO NOT start interactive flow in a web request
    raise Exception(
        "Google Drive authentication missing. Please run 'python3 manage.py setup_gdrive' "
        "to authorize the application once."
    )


def get_drive_service():
    """Returns an authenticated Google Drive API service."""
    from googleapiclient.discovery import build
    creds = _get_credentials()
    return build('drive', 'v3', credentials=creds)


def _find_or_create_folder(service, folder_name, parent_id=None):
    """Find a folder by name (under parent), or create it."""
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"

    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    files = results.get('files', [])

    if files:
        return files[0]['id']

    # Create the folder
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
    }
    if parent_id:
        file_metadata['parents'] = [parent_id]

    folder = service.files().create(body=file_metadata, fields='id').execute()
    logger.info(f"Created Google Drive folder: {folder_name} (ID: {folder.get('id')})")
    return folder.get('id')


def _get_target_folder(service, report_type, department_name=None):
    """
    Returns the folder ID for storing files.
    Structure: TIC_Doc_Platform / <report_type_folder> / [<department_name>]
    """
    root_id = _find_or_create_folder(service, ROOT_FOLDER_NAME)
    type_folder_name = SUBFOLDER_MAP.get(report_type, report_type)
    type_folder_id = _find_or_create_folder(service, type_folder_name, root_id)

    if department_name:
        return _find_or_create_folder(service, department_name, type_folder_id)
    return type_folder_id


def upload_document(file_obj, filename, report_type, department_name=None):
    """
    Upload a document to Google Drive.
    Converts .docx to Google Docs format on Drive.
    Returns (gdrive_file_id, gdrive_pdf_id, thumbnail_link).
    """
    from googleapiclient.http import MediaIoBaseUpload

    service = get_drive_service()
    folder_id = _get_target_folder(service, report_type, department_name)

    # Upload the file as Google Docs format
    file_metadata = {
        'name': filename,
        'parents': [folder_id],
        'mimeType': 'application/vnd.google-apps.document',  # Convert to Google Docs
    }

    content = file_obj.read()
    media = MediaIoBaseUpload(
        BytesIO(content),
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        resumable=True
    )

    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, name, webViewLink, thumbnailLink'
    ).execute()

    gdrive_file_id = uploaded_file.get('id')
    thumbnail_link = uploaded_file.get('thumbnailLink')
    logger.info(f"Uploaded document: {filename} → Drive ID: {gdrive_file_id}")

    # Export as PDF and upload separately (optional now that we use live links, but good for backup)
    gdrive_pdf_id = _export_as_pdf(service, gdrive_file_id, filename, folder_id)

    return gdrive_file_id, gdrive_pdf_id, thumbnail_link


def _export_as_pdf(service, doc_id, original_name, folder_id):
    """Export a Google Doc as PDF and save it on Drive."""
    from googleapiclient.http import MediaIoBaseUpload

    try:
        pdf_content = service.files().export(fileId=doc_id, mimeType='application/pdf').execute()

        pdf_name = os.path.splitext(original_name)[0] + ' (View Only).pdf'
        file_metadata = {
            'name': pdf_name,
            'parents': [folder_id],
        }

        media = MediaIoBaseUpload(
            BytesIO(pdf_content),
            mimetype='application/pdf',
            resumable=True
        )

        pdf_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        pdf_id = pdf_file.get('id')
        logger.info(f"Created PDF export: {pdf_name} → Drive ID: {pdf_id}")
        return pdf_id
    except Exception as e:
        logger.error(f"Error exporting PDF for {doc_id}: {e}")
        return None


def get_file_thumbnail(file_id):
    """Fetches the thumbnail link for a file."""
    try:
        service = get_drive_service()
        file_meta = service.files().get(fileId=file_id, fields='thumbnailLink').execute()
        return file_meta.get('thumbnailLink')
    except Exception as e:
        logger.error(f"Error fetching thumbnail for {file_id}: {e}")
        return None


def get_live_pdf_link(file_id):
    """
    Returns a link that exports the Google Doc to PDF on the fly.
    This ensures the PDF is always up-to-date with the latest edits.
    """
    return f"https://docs.google.com/document/d/{file_id}/export?format=pdf"


def get_file_view_link(file_id):
    """Get the web view link for a Google Drive file."""
    service = get_drive_service()
    file = service.files().get(fileId=file_id, fields='webViewLink').execute()
    return file.get('webViewLink', '')


def get_pdf_download_link(file_id):
    """Get a direct download link for a PDF file."""
    return f"https://drive.google.com/uc?export=download&id={file_id}"
