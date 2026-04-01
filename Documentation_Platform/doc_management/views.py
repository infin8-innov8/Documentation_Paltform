import json
import logging
import traceback

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from django.db.models import Q
from auth_autho.models import Department
from .models import Report

logger = logging.getLogger(__name__)


# ─── Permission Helpers ───

def _is_admin_or_president(user):
    """Admin & President have full access to everything."""
    if user.is_superuser:
        return True
    return user.role and user.role.role_name in ['Admin', 'President']


def _is_head(user):
    """Head has department-scoped access."""
    return user.role and user.role.role_name == 'Head of Department'


def _can_upload(user, department=None):
    """
    Check if user can upload to a specific department (or globally).
    - Admin/President: can upload anywhere.
    - Head: can only upload to their own department.
    """
    if _is_admin_or_president(user):
        return True
    if _is_head(user):
        if department is None:
            return True  # generic check; dept will be validated at upload time
        return user.department and user.department.department_id == department.department_id
    return False


def _can_view_department(user, department):
    """Check if user can view a specific department's documents."""
    if _is_admin_or_president(user):
        return True
    if _is_head(user):
        return user.department and user.department.department_id == department.department_id
    return False


def _can_modify(user, report):
    """Check if user can modify/delete a specific report."""
    if _is_admin_or_president(user):
        return True
    if _is_head(user) and report.department:
        return user.department and user.department.department_id == report.department.department_id
    return False


# ─── Views ───

@login_required
def home(request):
    return render(request, 'home.html')


@login_required
def idm_reports(request):
    user = request.user

    if _is_admin_or_president(user):
        departments = Department.objects.all()
        page_desc = 'Select a department below to view its Internal Departmental Meeting reports.'
    elif _is_head(user) and user.department:
        # Head only sees their own department
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


def _attach_gdrive_metadata(reports, user):
    """
    Helper to attach Google Drive thumbnails and live PDF links to reports.
    Uses batch fetching to minimize API calls.
    """
    from .gdrive_service import get_drive_service, get_live_pdf_link
    
    file_ids = [r.gdrive_file_id for r in reports if r.gdrive_file_id]
    if not file_ids:
        for report in reports:
            report.user_can_modify = _is_admin_or_president(user) or _can_modify(user, report)
        return reports

    try:
        service = get_drive_service()
        for report in reports:
            if report.gdrive_file_id:
                try:
                    # Individual fetch since files.list q doesn't support id
                    file_meta = service.files().get(fileId=report.gdrive_file_id, fields='thumbnailLink').execute()
                    report.thumbnail_url = file_meta.get('thumbnailLink')
                except Exception as e:
                    logger.warning(f"Failed to fetch thumbnail for {report.gdrive_file_id}: {e}")
            
            report.live_pdf_link = get_live_pdf_link(report.gdrive_file_id) if report.gdrive_file_id else None
            report.user_can_modify = _is_admin_or_president(user) or _can_modify(user, report)
    except Exception as e:
        logger.error(f"Error attaching Drive metadata: {e}")
        for report in reports:
            report.user_can_modify = _is_admin_or_president(user) or _can_modify(user, report)
    
    return reports


@login_required
def idm_dept_reports(request, dept_id):
    """Show reports for a specific department under IDM."""
    user = request.user
    department = get_object_or_404(Department, department_id=dept_id)

    # Permission: Admin/President see all; Head sees only own dept
    if not _can_view_department(user, department):
        raise PermissionDenied("You don't have access to this department's documents.")

    reports = Report.objects.filter(report_type='IDM', department=department, is_deleted=False).order_by('-uploaded_at')
    can_upload = _can_upload(user, department)

    reports = _attach_gdrive_metadata(reports, user)

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

    # ODM: only Admin/President can view
    if not _is_admin_or_president(user):
        raise PermissionDenied("You do not have permission to view ODM Reports.")

    reports = Report.objects.filter(report_type='ODM', is_deleted=False).order_by('-uploaded_at')
    can_upload = True  # Admin/President always can

    reports = _attach_gdrive_metadata(reports, user)

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

    if _is_admin_or_president(user):
        departments = Department.objects.all()
        page_desc = 'Select a department below to view its Monthly Progress reports.'
    elif _is_head(user) and user.department:
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
def monthly_dept_reports(request, dept_id):
    """Show monthly progress reports for a specific department."""
    user = request.user
    department = get_object_or_404(Department, department_id=dept_id)

    if not _can_view_department(user, department):
        raise PermissionDenied("You don't have access to this department's documents.")

    reports = Report.objects.filter(report_type='MONTHLY', department=department, is_deleted=False).order_by('-uploaded_at')
    can_upload = _can_upload(user, department)

    reports = _attach_gdrive_metadata(reports, user)

    return render(request, 'monthly_dept_reports.html', {
        'page_title': f'Monthly Progress — {department.department_name}',
        'page_desc': f'Monthly Progress reports for {department.department_name}.',
        'icon': '📈',
        'department': department,
        'reports': reports,
        'can_upload': can_upload,
        'report_type': 'MONTHLY',
    })


@login_required
def bootcamp_reports(request):
    user = request.user
    reports = Report.objects.filter(report_type='BOOTCAMP', is_deleted=False).order_by('-uploaded_at')
    can_upload = _is_admin_or_president(user) or _is_head(user)

    reports = _attach_gdrive_metadata(reports, user)

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
    user = request.user
    reports = Report.objects.filter(report_type='GUIDELINES', is_deleted=False).order_by('-uploaded_at')
    can_upload = _is_admin_or_president(user)

    reports = _attach_gdrive_metadata(reports, user)

    return render(request, 'guidelines.html', {
        'page_title': 'Guidelines & Other',
        'page_desc': 'Platform guidelines, documentation templates, and miscellaneous resources.',
        'icon': '📌',
        'reports': reports,
        'can_upload': can_upload,
        'report_type': 'GUIDELINES',
    })


@login_required
def search_documents(request):
    """Global search for documents across all categories."""
    query = request.GET.get('q', '').strip()
    user = request.user
    
    if not query:
        return redirect('home')

    # Base filter for text fields
    search_filter = Q(agenda__icontains=query) | Q(topic__icontains=query) | Q(original_filename__icontains=query)
    
    reports = Report.objects.filter(search_filter, is_deleted=False)
    
    # Permission Filtering
    if not _is_admin_or_president(user):
        # 1. Exclude ODM (Official Dept Meetings) - strictly Admin/President
        reports = reports.exclude(report_type='ODM')
        
        # 2. For IDM and Monthly, only show if it matches user's department
        if _is_head(user) and user.department:
            reports = reports.filter(
                Q(report_type__in=['BOOTCAMP', 'GUIDELINES']) |
                Q(department=user.department)
            )
        else:
            # Restricted to public-ish types if no department assigned
            reports = reports.filter(report_type__in=['BOOTCAMP', 'GUIDELINES'])

    reports = reports.order_by('-uploaded_at')
    reports = _attach_gdrive_metadata(reports, user)

    return render(request, 'search_results.html', {
        'page_title': f'Search Results: "{query}"',
        'query': query,
        'reports': reports,
        'icon': '🔍'
    })


# ─── Upload & Delete Endpoints ───

@require_POST
@login_required
def upload_report(request):
    """Handle file upload via AJAX. Returns JSON response."""
    user = request.user

    # Basic role check
    if not (_is_admin_or_president(user) or _is_head(user)):
        return JsonResponse({'success': False, 'error': 'You do not have permission to upload.'}, status=403)

    try:
        report_type = request.POST.get('report_type', '')
        date_str = request.POST.get('date_of_conduction', '')
        time_str = request.POST.get('time_of_conduction', '')
        participants_raw = request.POST.get('total_participants')
        total_participants = int(participants_raw) if participants_raw and participants_raw.isdigit() else None
        
        agenda = request.POST.get('agenda', '')
        topic = request.POST.get('topic', '')
        title = request.POST.get('title', '') # Unified title field
        
        # For Guidelines, if title is provided, use it as agenda/topic label
        if report_type == 'GUIDELINES' and title:
            agenda = title

        dept_id = request.POST.get('department_id')
        file = request.FILES.get('document')

        if not file:
            return JsonResponse({'success': False, 'error': 'No file uploaded.'}, status=400)

        # Enforce single file only
        if len(request.FILES.getlist('document')) > 1:
            return JsonResponse({'success': False, 'error': 'Only one file at a time is allowed.'}, status=400)

        # Validate file type (must be .docx)
        if not file.name.endswith('.docx'):
            return JsonResponse({'success': False, 'error': 'Only .docx files are accepted.'}, status=400)

        # Get department for IDM / Monthly
        department = None
        department_name = None
        if (report_type == 'IDM' or report_type == 'MONTHLY') and dept_id:
            department = get_object_or_404(Department, department_id=dept_id)
            department_name = department.department_name

            # Head can only upload to own department
            if _is_head(user) and not _is_admin_or_president(user):
                if not user.department or user.department.department_id != department.department_id:
                    return JsonResponse({'success': False, 'error': 'You can only upload to your own department.'}, status=403)

        # Upload to Google Drive
        from .gdrive_service import upload_document
        gdrive_file_id, gdrive_pdf_id, thumbnail_url = upload_document(
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
            date_of_conduction=date_str if date_str else None,
            time_of_conduction=time_str if time_str else None,
            total_participants=total_participants,
            agenda=agenda,
            topic=topic,
            gdrive_file_id=gdrive_file_id,
            gdrive_pdf_id=gdrive_pdf_id,
            original_filename=file.name,
        )

        # RAG Indexing
        try:
            from .rag_service import index_report_from_content
            file.seek(0)
            index_report_from_content(report, file.read())
        except Exception as e:
            logger.error(f"RAG Indexing failed for report {report.id}: {e}")

        return JsonResponse({
            'success': True,
            'message': f'Report "{file.name}" uploaded successfully.',
            'report_id': report.id,
        })

    except Exception as e:
        logger.exception("Upload error")
        error_msg = str(e)
        if "Google Drive authentication missing" in error_msg:
            return JsonResponse({'success': False, 'error': error_msg}, status=401)
        return JsonResponse({'success': False, 'error': f"An error occurred: {error_msg}"}, status=500)


@require_POST
@login_required
def delete_report(request, report_id):
    """Delete a report. Only Admin/President or Head of the same department."""
    user = request.user
    report = get_object_or_404(Report, id=report_id)

    if not _can_modify(user, report):
        return JsonResponse({'success': False, 'error': 'You do not have permission to delete this report.'}, status=403)

    report_name = report.original_filename
    report.is_deleted = True
    report.save()

    return JsonResponse({
        'success': True,
        'message': f'Report "{report_name}" deleted successfully.',
    })
 
 
@require_POST
@login_required
def chat_query(request):
    """Handle AI Chatbot queries with RAG and role-based filtering."""
    user = request.user
    query = request.POST.get('query', '').strip()
    
    if not query:
        return JsonResponse({'success': False, 'error': 'Query is empty.'}, status=400)
 
    try:
        # 1. Determine authorized reports for this user
        authorized_reports = Report.objects.filter(is_deleted=False)
        
        if not _is_admin_or_president(user):
            # Exclude ODM
            authorized_reports = authorized_reports.exclude(report_type='ODM')
            
            # Filter department-specific reports (IDM and Monthly)
            dept_filter = Q(report_type__in=['BOOTCAMP', 'GUIDELINES'])
            if _is_head(user) and user.department:
                dept_filter |= Q(department=user.department)
            
            authorized_reports = authorized_reports.filter(dept_filter)
 
        authorized_ids = list(authorized_reports.values_list('id', flat=True))
        
        # 2. RAG Search
        from .rag_service import search_relevant_chunks, generate_answer
        relevant_chunks = search_relevant_chunks(query, authorized_ids)
        
        # 3. Generate Answer
        answer = generate_answer(query, relevant_chunks)
        
        return JsonResponse({
            'success': True,
            'answer': answer,
            'sources': list(set([c.report.agenda or c.report.topic or c.report.original_filename for c in relevant_chunks]))
        })
        
    except Exception as e:
        logger.exception("Chat query error")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
