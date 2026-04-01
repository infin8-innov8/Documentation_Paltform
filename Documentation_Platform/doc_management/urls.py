from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('idm/', views.idm_reports, name='idm_reports'),
    path('idm/<int:dept_id>/', views.idm_dept_reports, name='idm_dept_reports'),
    path('odm/', views.odm_reports, name='odm_reports'),
    path('monthly-progress/', views.monthly_progress, name='monthly_progress'),
    path('monthly-progress/<int:dept_id>/', views.monthly_dept_reports, name='monthly_dept_reports'),
    path('bootcamp/', views.bootcamp_reports, name='bootcamp_reports'),
    path('guidelines/', views.guidelines, name='guidelines'),
    path('search/', views.search_documents, name='search_documents'),
    path('chat/', views.chat_query, name='chat_query'),
    path('upload-report/', views.upload_report, name='upload_report'),
    path('delete-report/<int:report_id>/', views.delete_report, name='delete_report'),
]
