from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db import models
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import requires_csrf_token
from .models import Subject 
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm
from .models import LecturerProfile
from .models import Subject
from .models import Profile, LecturerProfile
from blog.models import AcademicRequest
def get_lecturer_by_subject(request):
    subject = request.GET.get('subject')
    try:
        lecturer = LecturerProfile.objects.get(subject=subject)
        return JsonResponse({
            'lecturer_name': lecturer.user.get_full_name(),
            'lecturer_email': lecturer.user.email
        })
    except LecturerProfile.DoesNotExist:
        return JsonResponse({'error': 'Lecturer not found'}, status=404)

@login_required
def lecturer_requests(request):
    subject = request.user.lecturerprofile.subject.split(",")
    requests = AcademicRequest.objects.filter(subject__in=subject)
    return render(request, 'users/lecturer_requests.html', {'requests': requests})
    
from .models import Subject
import json

# users/views.py
def register(request):
    msg = None
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            if user.is_student:
                user.is_approved = True
            user.save()
            
            if user.is_lecturer:
                courses_json = form.cleaned_data.get('courses')
                print(f"Creating courses for lecturer: {user.username}")
                print(f"Courses JSON: {courses_json}")
                
                if courses_json:
                    try:
                        courses_list = json.loads(courses_json)
                        print(f"Parsed courses: {courses_list}")
                        
                        created_subjects = []
                        for course_name in courses_list:
                            course_name = course_name.strip()
                            if course_name:
                                subject = Subject.objects.create(
                                    name=course_name,
                                    department=user.department,
                                    lecturer=user
                                )
                                created_subjects.append(subject)
                                print(f"Created subject: {subject}")
                        
                        # Verify subjects were created
                        print(f"Total subjects created: {len(created_subjects)}")
                        
                        # Double-check by querying the database
                        db_subjects = Subject.objects.filter(lecturer=user)
                        print(f"Subjects in database for {user.username}: {list(db_subjects.values_list('name', flat=True))}")
                        
                    except (json.JSONDecodeError, TypeError) as e:
                        print(f"Error parsing courses: {e}")
                        import traceback
                        traceback.print_exc()
                else:
                    print("No courses data found in form")
            
            # Send welcome email
            send_mail(
                subject='Welcome to ISEND Your Academic Assistant!',
                message=f"Hi {user.username},\n\n"
                        "Welcome to iSend! We're excited to have you on board.\n\n"
                        "With iSend, you can easily submit academic requests, upload and receive documents, "
                        "and track the status of each request in real time – all in one place.\n\n"
                        "If you ever need help, our smart assistant is here to guide you step-by-step.\n\n"
                        "Let's make your academic life easier, more organized, and stress-free 🎓\n\n"
                        "Best wishes,\n"
                        "The iSend Team",
                from_email=None,
                recipient_list=[user.email],
                fail_silently=False,
            )

            if user.is_student:
                login(request, user)
                return redirect('blog-home')
            elif user.is_lecturer:
                msg = "Lecturer account created and waiting approval"
                return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form, 'msg': msg})

def login_view(request):
    msg = None
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            # תקן את התנאי כאן
            if user.is_lecturer or user.is_secretary or user.is_student:  # ← תקן כאן
                login(request, user)

                # Send login email
                send_mail(
                    subject='🔐 New Login Detected',
                    message=f'Hi {user.username}, you have just logged into your ISEND account.',
                    from_email=None,
                    recipient_list=[user.email],
                    fail_silently=False,
                )

                # Redirect based on user type
                if user.is_secretary:
                    return redirect('secretary-dashboard')
                elif user.is_student:
                    return redirect('blog-home')
                elif user.is_lecturer:
                    return redirect('lecturer_dashboard')
                elif user.is_superuser:
                    return redirect('adminpage')
            else:
                msg = "Account not approved or invalid user type."
        else:
            msg = "Invalid username or password."
    return render(request, 'users/login.html', {'form': form, 'msg': msg})

@login_required
def profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST,
                                   request.FILES,
                                   instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Your account has been updated!')
            return redirect('profile')

    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }

    return render(request, 'users/profile.html', context)



@requires_csrf_token
def csrf_failure(request, reason=""):
    return render(request, 'users/csrf_failure.html', {'reason': reason}, status=403)
@login_required
def update_request_status(request, request_id):
    if not request.user.is_lecturer:
        messages.error(request, 'Access denied.')
        return redirect('blog-home')
    
    if request.method == "POST":
        # הסר את הפילטר assigned_to זמנית
        academic_request = get_object_or_404(AcademicRequest, id=request_id)
        
        new_status = request.POST.get("status")
        lecturer_note = request.POST.get("lecturer_note", "")
        update_deadline = request.POST.get("update_deadline")
        
        if new_status in dict(AcademicRequest.STATUS_CHOICES).keys():
            academic_request.status = new_status
            
            if lecturer_note:
                academic_request.lecturer_note = lecturer_note
            
            if update_deadline and new_status == 'need_update':
                academic_request.update_deadline = update_deadline
            
            academic_request.save()
            messages.success(request, 'Request status updated successfully.')
        else:
            messages.error(request, 'Invalid status selected.')
    
    return redirect("lecturer_dashboard")
@login_required
def get_request_details(request, request_id):
    """AJAX view to get request details"""
    if not request.user.is_lecturer:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # הסר את הפילטר assigned_to זמנית
    academic_request = get_object_or_404(AcademicRequest, id=request_id)
    
    data = {
        'id': academic_request.id,
        'student_name': academic_request.student.get_full_name() or academic_request.student.username,
        'subject': academic_request.subject,
        'request_type': academic_request.request_type,
        'request_text': academic_request.request_text,
        'status': academic_request.status,
        'lecturer_note': academic_request.lecturer_note or '',
        'created_at': academic_request.created_at.strftime('%d/%m/%Y %H:%M'),
        'update_deadline': academic_request.update_deadline.strftime('%Y-%m-%d') if academic_request.update_deadline else '',
        'update_deadline_display': academic_request.update_deadline.strftime('%d/%m/%Y') if academic_request.update_deadline else '',
        'is_past_deadline': academic_request.is_past_deadline() if academic_request.update_deadline else False,
    }
    
    return JsonResponse(data)
@login_required
def lecturer_dashboard(request):
    """
    Display the lecturer dashboard with academic requests and handle request updates.
    """
    # Check if user is a lecturer
    if not request.user.is_lecturer:
        messages.error(request, 'Access denied. This page is for lecturers only.')
        return redirect('blog-home')
    
    # Handle form submission for request update
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        status = request.POST.get('status')
        lecturer_note = request.POST.get('lecturer_note')
        update_deadline = request.POST.get('update_deadline')
        
        # Get the academic request
        academic_request = get_object_or_404(AcademicRequest, id=request_id)
        
        # Update the request
        academic_request.status = status
        academic_request.lecturer_note = lecturer_note
        
        # Update deadline if status is 'need_update' and deadline provided
        if status == 'need_update' and update_deadline:
            academic_request.update_deadline = update_deadline
        elif status != 'need_update':
            # Clear deadline if status is not 'need_update'
            academic_request.update_deadline = None
        
        academic_request.save()
@login_required
def lecturer_dashboard(request):
    """
    Display the lecturer dashboard with academic requests and handle request updates.
    """
    # Check if user is a lecturer
    if not request.user.is_lecturer:
        messages.error(request, 'Access denied. This page is for lecturers only.')
        return redirect('blog-home')
    
    # Handle form submission for request update
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        status = request.POST.get('status')
        lecturer_note = request.POST.get('lecturer_note')
        update_deadline = request.POST.get('update_deadline')
        
        # Get the academic request
        academic_request = get_object_or_404(AcademicRequest, id=request_id)
        
        # Update the request
        academic_request.status = status
        academic_request.lecturer_note = lecturer_note
        
        # Update deadline if status is 'need_update' and deadline provided
        if status == 'need_update' and update_deadline:
            academic_request.update_deadline = update_deadline
        elif status != 'need_update':
            # Clear deadline if status is not 'need_update'
            academic_request.update_deadline = None
        
        academic_request.save()
        
        # Add success message
        messages.success(request, 'הבקשה עודכנה בהצלחה')
        
        # Redirect to avoid form resubmission
        return redirect('lecturer_dashboard')
    
    # Get ALL academic requests (remove assigned_to filter temporarily)
    academic_requests = AcademicRequest.objects.all().order_by('-created_at')
    
    # Get statistics for ALL requests
    pending_requests = AcademicRequest.objects.filter(status='pending')
    in_progress_requests = AcademicRequest.objects.filter(status='in_progress')
    approved_requests = AcademicRequest.objects.filter(status='approved')
    rejected_requests = AcademicRequest.objects.filter(status='rejected')
    
    # Get recent requests
    recent_requests = academic_requests[:5]
    
    # Get requests with upcoming deadlines
    upcoming_deadlines = academic_requests.filter(
        update_deadline__isnull=False,
        update_deadline__gte=timezone.now()
    ).order_by('update_deadline')[:5]
    
    context = {
        'academic_requests': academic_requests,
        'pending_requests': pending_requests,
        'in_progress_requests': in_progress_requests,
        'approved_requests': approved_requests,
        'rejected_requests': rejected_requests,
        'recent_requests': recent_requests,
        'upcoming_deadlines': upcoming_deadlines,
    }
    
    return render(request, 'users/lecturer_dashboard.html', context)
@login_required
def request_detail(request, request_id):
    """
    AJAX endpoint to get request details for the modal
    """
    # Check if user has a lecturer profile
    try:
        lecturer_profile = request.user.lecturerprofile
    except LecturerProfile.DoesNotExist:
        # Return error response
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Get the academic request
    academic_request = get_object_or_404(AcademicRequest, id=request_id)
    
    # Prepare the response data
    data = {
        'id': academic_request.id,
        'student_name': academic_request.student.get_full_name(),
        'subject': academic_request.subject,
        'request_type': academic_request.request_type,
        'request_text': academic_request.request_text,
        'lecturer_note': academic_request.lecturer_note,
        'status': academic_request.status,
        'created_at': academic_request.created_at.strftime('%d/%m/%Y'),
        'is_past_deadline': academic_request.is_past_deadline(),
    }
    
    # Add deadline data if it exists
    if academic_request.update_deadline:
        data['update_deadline'] = academic_request.update_deadline.strftime('%d/%m/%Y')
        data['update_deadline_raw'] = academic_request.update_deadline.strftime('%Y-%m-%d')
    else:
        data['update_deadline'] = None
        data['update_deadline_raw'] = None
    
    return JsonResponse(data)



from django.utils import timezone
from datetime import timedelta

def return_for_update(request, request_id):
    if request.method == 'POST':
        req = get_object_or_404(AcademicRequest, id=request_id)
        note = request.POST.get('lecturer_note', '')
        req.lecturer_note = note
        req.status = 'need_update'
        req.update_deadline = timezone.now() + timedelta(days=5)
        req.save()
        return redirect('lecturer_requests')