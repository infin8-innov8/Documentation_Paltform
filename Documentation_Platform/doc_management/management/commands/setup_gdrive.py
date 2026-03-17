import os
from pathlib import Path
from django.core.management.base import BaseCommand
from google_auth_oauthlib.flow import InstalledAppFlow

class Command(BaseCommand):
    help = 'Perform one-time Google Drive OAuth setup to generate token.json'

    def handle(self, *args, **options):
        BASE_DIR = Path(__file__).resolve().parent.parent.parent
        CLIENT_SECRET_FILE = BASE_DIR / 'client_secret.json'
        TOKEN_FILE = BASE_DIR / 'token.json'
        SCOPES = ['https://www.googleapis.com/auth/drive']

        if not CLIENT_SECRET_FILE.exists():
            self.stdout.write(self.style.ERROR(f'FileNotFound: {CLIENT_SECRET_FILE} not found.'))
            self.stdout.write('Please ensure client_secret.json is in the doc_management directory.')
            return

        self.stdout.write('\nGoogle Drive OAuth Setup')
        self.stdout.write('------------------------')
        self.stdout.write('This command will open a browser window to authorize the TIC platform.')
        self.stdout.write('Once completed, a token.json file will be created to allow silent uploads.\n')

        # Since this is a terminal command, we can safely use any port or random port
        flow = InstalledAppFlow.from_client_secrets_file(
            str(CLIENT_SECRET_FILE), SCOPES
        )

        try:
            self.stdout.write('Opening browser for authentication...')
            # Strictly use port 8090 to match Google Console whitelist
            creds = flow.run_local_server(port=8090)
            
            with open(TOKEN_FILE, 'w') as f:
                f.write(creds.to_json())
            
            self.stdout.write(self.style.SUCCESS(f'\nSuccess! token.json created at {TOKEN_FILE}'))
            self.stdout.write('You can now upload documents without being prompted to sign in again.\n')
            
        except OSError as e:
            if e.errno == 98:
                self.stdout.write(self.style.ERROR('\nPort 8090 is still busy.'))
                self.stdout.write('Please run: fuser -k 8090/tcp\nThen try again.')
            else:
                raise e
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nAn error occurred: {e}'))
