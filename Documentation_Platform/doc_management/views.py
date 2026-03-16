from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def home(request):
    return render(request, 'home.html')

@login_required
def idm_reports(request):
    return render(request, 'tab_view.html', {'page_title': 'IDM Reports', 'page_desc': 'View and manage Internal Departmental Meeting reports and minutes.', 'icon': '📋'})

@login_required
def odm_reports(request):
    return render(request, 'tab_view.html', {'page_title': 'ODM Reports', 'page_desc': 'Access Official Documentation Management reports for your department.', 'icon': '📁'})

@login_required
def monthly_progress(request):
    return render(request, 'tab_view.html', {'page_title': 'Monthly Progress', 'page_desc': 'Track and evaluate monthly team and project progress reports.', 'icon': '📈'})

@login_required
def bootcamp_reports(request):
    return render(request, 'tab_view.html', {'page_title': 'Bootcamp Reports', 'page_desc': 'Review training metrics, participant feedback, and bootcamp summaries.', 'icon': '🎓'})

@login_required
def guidelines(request):
    return render(request, 'tab_view.html', {'page_title': 'Guidelines & Other', 'page_desc': 'Access platform guidelines, documentation templates, and miscellaneous resources.', 'icon': '📌'})
