from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from users import views as user_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', user_views.register, name='register'),
    path('login/', user_views.login_view, name='login'),
    path('profile/', user_views.profile, name='profile'),
    path('logout/', auth_views.LogoutView.as_view(template_name='users/logout.html'), name='logout'),

    # Blog app URLs
path('', include('blog.urls')),
    #password
    path('password/', user_views.password_management, name='password_management'),
    path('forgot-password/',user_views.forgot_password, name='forgot_password'),
    path('password/change/', user_views.change_password_direct, name='change_password_direct'),

# Add this line to handle the frontend's expected URL format:
path('lecturer_get_request_details/<int:request_id>/', user_views.lecturer_get_request_details, name='lecturer_get_request_details_alt'),
    # Lecturer-specific views# Add this to your urlpatterns
path('download/<int:request_id>/<str:file_type>/', user_views.download_file, name='download_file'),
    path('lecturer/dashboard/', user_views.lecturer_dashboard, name='lecturer_dashboard'),
    path('lecturer/requests/', user_views.lecturer_requests, name='lecturer_requests'),
    path('lecturer/dashboard/', user_views.lecturer_dashboard, name='lecturer_dashboard'),
    path('lecturer/update_request_status/<int:request_id>/', user_views.update_request_status, name='lecturer_update_request_status'),
    path('lecturer/get-request-details/<int:request_id>/', user_views.lecturer_get_request_details, name='lecturer_get_request_details'),
    # Add this line to your urlpatterns:
path('users/lecturer/update-request-status/<int:request_id>/', user_views.update_request_status, name='users_lecturer_update_request_status'),
    path('get-lecturer/', user_views.get_lecturer_by_subject, name='get_lecturer_by_subject'),
    path('secretary/users/', user_views.secretary_user_list, name='secretary_user_list'),
    path('secretary/users/delete/<int:user_id>/', user_views.secretary_delete_user, name='secretary_delete_user'),
   
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
