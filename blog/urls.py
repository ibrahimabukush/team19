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

]