from django.urls import path
from . import views
from .views import chatbot_response, chat_history

urlpatterns = [
    # Error reporting
    path('get-department-lecturers/', views.get_department_lecturers, name='get_department_lecturers'),
    path('error-report/', views.error_report_form, name='error_report_form'),
    path('submit-error-report/', views.submit_error_report, name='submit_error_report'),
    path('my-error-reports/', views.my_error_reports, name='my_error_reports'),
    
    # Request details
    path('get_request_details/<int:request_id>/', views.get_request_details, name='get_request_details'),
    
    # Basic pages
    path('', views.home, name='blog-home'),
    path('about/', views.about, name='blog-about'),
    path('technicalmanagement/', views.technicalmanagement, name='technicalmanagement'),
    path('services/', views.services, name='blog-services'),
    path('contact/', views.contact, name='contact'),
    
    # File downloads
    path('download/<int:request_id>/<str:file_type>/', views.download_file, name='download_file'),
    
    # Chatbot
    path('chatbot/', chatbot_response, name='chatbot_response'),
    path('chat_history/', chat_history, name='chat_history'),
    
    # Academic requests
    path('academic-request/', views.academic_request, name='academic-request'),
    path('submit-request/', views.submit_request, name='submit_request'),
    path("api/submit-request", views.submit_request, name="submit_request"),
    
    # FIXED: Schedule requests - no more conflicts
    path('schedule_request/', views.schedule_request, name='schedule_request'),  # Main form page
    path('schedule_requests/list/', views.schedule_requests_list, name='schedule_requests_list'),  # List view
    path('schedule_requests/<int:request_id>/', views.schedule_request_detail, name='schedule_request_detail'),  # Detail view
    path('submit-schedule_requests/', views.submit_schedule_request, name='submit_schedule_requests'),  # Submit endpoint
    
    # Personal requests
    path('personal-requests/', views.personal_requests, name='personal_requests'),
    path('submit-personal_requests/', views.submit_personal_requests, name='submit_personal_requests'),
    path('personal-request/<int:request_id>/', views.personal_request_detail, name='personal_request_detail'),
    path('personal-request-list/', views.personal_request_list, name='personal_request_list'),
    
    # Tracking
    path('tracking/', views.tracking, name='tracking'),
    path('student/tracking/', views.tracking, name='student_tracking'),
    
    # Secretary dashboard
    path('secretary_dashboard/', views.secretary_dashboard, name='secretary_dashboard'),
    path('secretary/delete_request/<int:request_id>/', views.secretary_delete_request, name='secretary_delete_request'),
    path('secretary/request/<int:request_id>/', views.secretary_get_request_details, name='secretary_get_request_details'),
    path('schedule_requests/', views.schedule_request, name='schedule_requests'),
    # API endpoints
    path('api/subjects/', views.get_subjects_by_department, name='get_subjects'),
    path('get-subjects-by-department/', views.get_subjects_by_department, name='get-subjects-by-department'),
    path('get-lecturer/', views.get_lecturer, name='get_lecturer'),
    path('update_request_status/<int:request_id>/', views.update_request_status, name='update_request_status'),
]