import os
from django.core.management.base import BaseCommand
from doc_management.models import Report
from doc_management.rag_service import index_report_from_content
from doc_management.gdrive_service import get_drive_service
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Re-indexes all existing documents to include Agenda and Topic metadata in AI context.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting full re-indexing of all documents...'))
        
        reports = Report.objects.filter(is_deleted=False)
        count = reports.count()
        
        if count == 0:
            self.stdout.write(self.style.WARNING('No active reports found to re-index.'))
            return

        service = get_drive_service()
        
        for i, report in enumerate(reports, 1):
            if not report.gdrive_file_id:
                self.stdout.write(self.style.WARNING(f'[{i}/{count}] Skipping {report.original_filename} (No Drive ID)'))
                continue

            self.stdout.write(f'[{i}/{count}] Indexing: {report.agenda or report.topic or report.original_filename}...')
            
            try:
                # Need to fetch content from Google Drive since we don't store it locally
                file_content = service.files().export(fileId=report.gdrive_file_id, mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document').execute()
                
                index_report_from_content(report, file_content)
                self.stdout.write(self.style.SUCCESS(f'Successfully re-indexed {report.id}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to index {report.id}: {e}'))

        self.stdout.write(self.style.SUCCESS('\nRe-indexing complete!'))
