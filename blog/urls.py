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


]