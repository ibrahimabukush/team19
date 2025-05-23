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
    #password
    path('password/', user_views.password_management, name='password_management'),
    path('forgot-password/',user_views.forgot_password, name='forgot_password'),
    path('password/change/', user_views.change_password_direct, name='change_password_direct'),

    path('logout/', auth_views.LogoutView.as_view(template_name='users/logout.html'), name='logout'),

    # Blog app URLs
    path('', include('blog.urls')),
     path('password/', user_views.password_management, name='password_management'),
    path('password/forgot/', user_views.forgot_password, name='forgot_password'),

    # Lecturer-specific views
    path('lecturer/dashboard/', user_views.lecturer_dashboard, name='lecturer_dashboard'),
    path('lecturer/requests/', user_views.lecturer_requests, name='lecturer_requests'),
    path('lecturer/request/<int:request_id>/return/', user_views.return_for_update, name='return_for_update'),
    path('lecturer/request/<int:request_id>/update-status/', user_views.update_request_status, name='update_request_status'),

    path('get-lecturer/', user_views.get_lecturer_by_subject, name='get_lecturer_by_subject'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
