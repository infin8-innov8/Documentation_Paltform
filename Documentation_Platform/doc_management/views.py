from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.core.exceptions import PermissionDenied
from auth_autho.models import Department

@login_required
def home(request):
    return render(request, 'home.html')

@login_required
def idm_reports(request):
    user = request.user
    
    # If user is Admin or President, show all departments
    if user.is_superuser or (user.role and user.role.role_name in ['Admin', 'President']):
        departments = Department.objects.all()
        page_desc = 'Select a department below to view its Internal Departmental Meeting reports.'
    # For Head/Coordinator, only show their own department
    elif user.department:
        departments = Department.objects.filter(department_id=user.department.department_id)
        page_desc = f'Viewing Internal Departmental Meeting reports for {user.department.department_name}.'
    # Fallback for users without a department
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
def odm_reports(request):
    user = request.user
    if not (user.is_superuser or (user.role and user.role.role_name in ['Admin', 'President'])):
        raise PermissionDenied("You do not have permission to view ODM Reports.")
    return render(request, 'tab_view.html', {'page_title': 'ODM Reports', 'page_desc': 'Access Official Documentation Management reports.', 'icon': '📁'})

@login_required
def monthly_progress(request):
    user = request.user
    
    # If user is Admin or President, show all departments
    if user.is_superuser or (user.role and user.role.role_name in ['Admin', 'President']):
        departments = Department.objects.all()
        page_desc = 'Select a department below to view its Monthly Progress reports.'
    # For Head/Coordinator, only show their own department
    elif user.department:
        departments = Department.objects.filter(department_id=user.department.department_id)
        page_desc = f'Viewing Monthly Progress reports for {user.department.department_name}.'
    # Fallback for users without a department
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
    return render(request, 'tab_view.html', {'page_title': 'Bootcamp Reports', 'page_desc': 'Review training metrics, participant feedback, and bootcamp summaries.', 'icon': '🎓'})

@login_required
def guidelines(request):
    return render(request, 'tab_view.html', {'page_title': 'Guidelines & Other', 'page_desc': 'Access platform guidelines, documentation templates, and miscellaneous resources.', 'icon': '📌'})
