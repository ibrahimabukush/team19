from django.urls import path
from . import views
from .views import chatbot_response
from .views import chat_history



urlpatterns = [
    path('', views.home, name='blog-home'),
    path('about/', views.about, name='blog-about'),
    path('technicalmanagement/',views.technicalmanagement, name='technicalmanagement'),
     path('services/', views.services, name='blog-services'),
    path('contact/', views.contact, name='contact'),
    path('contact/', views.contact, name='blog-contact'),
     path('chatbot/', chatbot_response, name='chatbot_response'),
    path('chat_history/', chat_history, name='chat_history'),
    path("api/submit-request", views.submit_request, name="submit_request"),
    path('academic-request/', views.academic_request, name='academic-request'),
    path('schedule-request/', views.schedule_request, name='schedule_request'),
    path('student/tracking/', views.tracking, name='student_tracking'),
 path('schedule-request/', views.schedule_request_view, name='schedule_request'),
    path('schedule-request/submit/', views.submit_schedule_request, name='submit_schedule_request'),
    path('schedule-requests/', views.schedule_requests_list, name='schedule_requests_list'),
    path('schedule-request/<int:request_id>/', views.schedule_request_detail, name='schedule_request_detail'),
    path('secretary-dashboard/', views.secretary_dashboard, name='secretary-dashboard'),
    # path('update-request-status/<int:request_id>/', views.update_request_status, name='update-request-status'),
    # path('secretary-request/<int:request_id>/', views.secretary_request_detail, name='secretary-request-detail'),
    path('api/subjects/', views.get_subjects_by_department, name='get_subjects'),
path('get-lecturer/', views.get_lecturer, name='get_lecturer'),
path('submit-request/', views.submit_request, name='submit_request'),
       # Academic Request URLs
    path('submit-request/', views.submit_request, name='submit-request'),
    path('get-lecturer/', views.get_lecturer, name='get-lecturer'),
    path('get-subjects-by-department/', views.get_subjects_by_department, name='get-subjects-by-department'),
    path('tracking/', views.tracking, name='tracking'),
    #   path('send-student-message/', views.send_student_message, name='send_student_message'),
    path('update-request-status/<int:request_id>/', views.update_request_status, name='update_request_status'),
    # Schedule Request URLs
        path('chatbot/', views.chatbot_response, name='chatbot_response'),

    path('schedule-request/', views.schedule_request_view, name='schedule-request'),
    path('submit-schedule-request/', views.submit_schedule_request, name='submit-schedule-request'),
    path('schedule-requests/', views.schedule_requests_list, name='schedule-requests-list'),
    path('schedule-request/<int:request_id>/', views.schedule_request_detail, name='schedule-request-detail'),
    # Technical Management URLs
    path('technicalmanagement/', views.technicalmanagement, name='technicalmanagement'),
    path('submit-error-report/', views.submit_error_report, name='submit-error-report'),
    path('error-reports/', views.error_reports_list, name='error-reports-list'),
    path('update-error-report/<int:report_id>/', views.update_error_report_status, name='update-error-report-status'),
    # Secretary Dashboard
    path('secretary-dashboard/', views.secretary_dashboard, name='secretary-dashboard'),
]
