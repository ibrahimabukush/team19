from django.urls import path
from . import views
from .views import chatbot_response
from .views import chat_history


urlpatterns = [
    path('', views.home, name='blog-home'),
    path('about/', views.about, name='blog-about'),
     path('services/', views.services, name='blog-services'),
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
    path('update-request-status/<int:request_id>/', views.update_request_status, name='update-request-status'),
    path('secretary-request/<int:request_id>/', views.secretary_request_detail, name='secretary-request-detail'),
]