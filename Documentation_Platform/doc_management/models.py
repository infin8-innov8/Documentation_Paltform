from django.db import models
from django.conf import settings
from auth_autho.models import Department


class Report(models.Model):
    REPORT_TYPE_CHOICES = [
        ('IDM', 'Inter Department Meeting'),
        ('ODM', 'Official Department Meeting'),
        ('BOOTCAMP', 'Bootcamp'),
        ('MONTHLY', 'Monthly Progress'),
        ('GUIDELINES', 'Guidelines & Other'),
    ]

    report_type = models.CharField(max_length=10, choices=REPORT_TYPE_CHOICES)
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True,
        help_text='Required for IDM reports only.'
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )

    # Metadata - now optional for Guidelines
    date_of_conduction = models.DateField(null=True, blank=True)
    time_of_conduction = models.TimeField(null=True, blank=True)
    total_participants = models.PositiveIntegerField(null=True, blank=True, default=1)

    # IDM / ODM specific
    agenda = models.CharField(max_length=500, blank=True, default='')

    # Bootcamp specific
    topic = models.CharField(max_length=500, blank=True, default='')

    # Google Drive references
    gdrive_file_id = models.CharField(max_length=255, blank=True, default='')
    gdrive_pdf_id = models.CharField(max_length=255, blank=True, default='')
    original_filename = models.CharField(max_length=255, blank=True, default='')

    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        label = self.agenda or self.topic or self.original_filename
        return f"[{self.report_type}] {label} ({self.uploaded_at:%Y-%m-%d})"


class ReportChunk(models.Model):
    """Stores text chunks and embeddings for RAG."""
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='chunks')
    chunk_text = models.TextField()
    embedding = models.JSONField() # Store list of floats

    def __str__(self):
        return f"Chunk for {self.report.original_filename}"
