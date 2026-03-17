import json
import logging
import traceback

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from auth_autho.models import Department
from .models import Report

logger = logging.getLogger(__name__)


def _can_upload(user):
    """Check if user is Admin, President, or Head."""
    if user.is_superuser:
        return True
    if user.role and user.role.role_name in ['Admin', 'President', 'Head']:
        return True
    return False


@login_required
def home(request):
    return render(request, 'home.html')


@login_required
def idm_reports(request):
    user = request.user

    if user.is_superuser or (user.role and user.role.role_name in ['Admin', 'President']):
        departments = Department.objects.all()
        page_desc = 'Select a department below to view its Internal Departmental Meeting reports.'
    elif user.department:
        departments = Department.objects.filter(department_id=user.department.department_id)
        page_desc = f'Viewing Internal Departmental Meeting reports for {user.department.department_name}.'
    else:
        departments = Department.objects.none()
        page_desc = 'You do not have a department assigned.'

    return render(request, 'idm_reports.html', {
        'page_title': 'IDM Reports',
        'page_desc': page_desc,
        'icon': '📋',
        'departments': departments
    })


@login_required
def idm_dept_reports(request, dept_id):
    """Show reports for a specific department under IDM."""
    user = request.user
    department = get_object_or_404(Department, department_id=dept_id)

    # Only allow access to own department, unless Admin/President/superuser
    if not (user.is_superuser or (user.role and user.role.role_name in ['Admin', 'President'])):
        if not user.department or user.department.department_id != dept_id:
            raise PermissionDenied("You don't have access to this department.")

    reports = Report.objects.filter(report_type='IDM', department=department)
    can_upload = _can_upload(user)

    return render(request, 'idm_dept_reports.html', {
        'page_title': f'IDM — {department.department_name}',
        'page_desc': f'Inter Department Meeting reports for {department.department_name}.',
        'icon': '📋',
        'department': department,
        'reports': reports,
        'can_upload': can_upload,
        'report_type': 'IDM',
    })


@login_required
def odm_reports(request):
    user = request.user
    if not (user.is_superuser or (user.role and user.role.role_name in ['Admin', 'President'])):
        raise PermissionDenied("You do not have permission to view ODM Reports.")

    reports = Report.objects.filter(report_type='ODM')
    can_upload = _can_upload(user)

    return render(request, 'odm_reports.html', {
        'page_title': 'ODM Reports',
        'page_desc': 'Official Department Meeting reports.',
        'icon': '📁',
        'reports': reports,
        'can_upload': can_upload,
        'report_type': 'ODM',
    })


@login_required
def monthly_progress(request):
    user = request.user

    if user.is_superuser or (user.role and user.role.role_name in ['Admin', 'President']):
        departments = Department.objects.all()
        page_desc = 'Select a department below to view its Monthly Progress reports.'
    elif user.department:
        departments = Department.objects.filter(department_id=user.department.department_id)
        page_desc = f'Viewing Monthly Progress reports for {user.department.department_name}.'
    else:
        departments = Department.objects.none()
        page_desc = 'You do not have a department assigned.'

    return render(request, 'monthly_progress.html', {
        'page_title': 'Monthly Progress',
        'page_desc': page_desc,
        'icon': '📈',
        'departments': departments
    })


@login_required
def bootcamp_reports(request):
    reports = Report.objects.filter(report_type='BOOTCAMP')
    can_upload = _can_upload(request.user)

    return render(request, 'bootcamp_reports.html', {
        'page_title': 'Bootcamp Reports',
        'page_desc': 'Training sessions, workshops, and bootcamp summaries.',
        'icon': '🎓',
        'reports': reports,
        'can_upload': can_upload,
        'report_type': 'BOOTCAMP',
    })


@login_required
def guidelines(request):
    return render(request, 'tab_view.html', {
        'page_title': 'Guidelines & Other',
        'page_desc': 'Access platform guidelines, documentation templates, and miscellaneous resources.',
        'icon': '📌'
    })


@require_POST
@login_required
def upload_report(request):
    """Handle file upload via AJAX. Returns JSON response."""
    user = request.user

    if not _can_upload(user):
        return JsonResponse({'success': False, 'error': 'You do not have permission to upload.'}, status=403)

    try:
        report_type = request.POST.get('report_type', '')
        date_str = request.POST.get('date_of_conduction', '')
        time_str = request.POST.get('time_of_conduction', '')
        total_participants = int(request.POST.get('total_participants', 1))
        agenda = request.POST.get('agenda', '')
        topic = request.POST.get('topic', '')
        dept_id = request.POST.get('department_id')
        file = request.FILES.get('document')

        if not file:
            return JsonResponse({'success': False, 'error': 'No file uploaded.'}, status=400)

        # Validate file type (must be .docx)
        if not file.name.endswith('.docx'):
            return JsonResponse({'success': False, 'error': 'Only .docx files are accepted.'}, status=400)

        # Get department for IDM
        department = None
        department_name = None
        if report_type == 'IDM' and dept_id:
            department = get_object_or_404(Department, department_id=dept_id)
            department_name = department.department_name

        # Upload to Google Drive
        from .gdrive_service import upload_document
        gdrive_file_id, gdrive_pdf_id = upload_document(
            file_obj=file,
            filename=file.name,
            report_type=report_type,
            department_name=department_name
        )

        # Create DB record
        report = Report.objects.create(
            report_type=report_type,
            department=department,
            uploaded_by=user,
            date_of_conduction=date_str,
            time_of_conduction=time_str,
            total_participants=total_participants,
            agenda=agenda,
            topic=topic,
            gdrive_file_id=gdrive_file_id,
            gdrive_pdf_id=gdrive_pdf_id,
            original_filename=file.name,
        )

        return JsonResponse({
            'success': True,
            'message': f'Report "{file.name}" uploaded successfully.',
            'report_id': report.id,
        })

    except Exception as e:
        logger.error(f"Upload error: {traceback.format_exc()}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
