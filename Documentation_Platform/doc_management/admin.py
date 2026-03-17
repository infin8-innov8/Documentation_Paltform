from django.contrib import admin
from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('report_type', 'department', 'uploaded_by', 'date_of_conduction', 'uploaded_at')
    list_filter = ('report_type', 'department')
    search_fields = ('agenda', 'topic', 'original_filename')
    readonly_fields = ('gdrive_file_id', 'gdrive_pdf_id', 'uploaded_at')

