from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('idm/', views.idm_reports, name='idm_reports'),
    path('odm/', views.odm_reports, name='odm_reports'),
    path('monthly-progress/', views.monthly_progress, name='monthly_progress'),
    path('bootcamp/', views.bootcamp_reports, name='bootcamp_reports'),
    path('guidelines/', views.guidelines, name='guidelines'),
]
