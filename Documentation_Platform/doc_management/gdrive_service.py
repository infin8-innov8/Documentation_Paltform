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


def _get_credentials():
    """
    Get or refresh Google Drive credentials.
    On first run, this will open a browser-based consent flow.
    Subsequent runs use the cached token.json.
    """
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CLIENT_SECRET_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save for future runs
        with open(TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())

    return creds


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
    Returns (gdrive_file_id, gdrive_pdf_id).
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
        fields='id, name, webViewLink'
    ).execute()

    gdrive_file_id = uploaded_file.get('id')
    logger.info(f"Uploaded document: {filename} → Drive ID: {gdrive_file_id}")

    # Export as PDF and upload separately
    gdrive_pdf_id = _export_as_pdf(service, gdrive_file_id, filename, folder_id)

    return gdrive_file_id, gdrive_pdf_id


def _export_as_pdf(service, doc_id, original_name, folder_id):
    """Export a Google Doc as PDF and save it on Drive."""
    from googleapiclient.http import MediaIoBaseUpload

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


def get_file_view_link(file_id):
    """Get the web view link for a Google Drive file."""
    service = get_drive_service()
    file = service.files().get(fileId=file_id, fields='webViewLink').execute()
    return file.get('webViewLink', '')


def get_pdf_download_link(file_id):
    """Get a direct download link for a PDF file."""
    return f"https://drive.google.com/uc?export=download&id={file_id}"
