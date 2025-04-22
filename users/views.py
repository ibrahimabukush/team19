from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm
from .models import Profile
from django.contrib.auth import authenticate, login
from .forms import UserRegisterForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import requires_csrf_token
from django.core.mail import send_mail
from django.contrib.auth.models import User

from django.http import JsonResponse
from .models import LecturerProfile

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
from blog.models import AcademicRequest

@login_required
def lecturer_requests(request):
    subject = request.user.lecturerprofile.subject.split(",")
    requests = AcademicRequest.objects.filter(subject__in=subject)
    return render(request, 'users/lecturer_requests.html', {'requests': requests})
def register(request):
    msg = None
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            if user.is_student:
                user.is_approved = True
            user.save()

            # Send welcome email
            send_mail(
                subject='Welcome to ISEND Your Academic Assistant!',
                message= f"Hi {user.username},\n\n"
        "Welcome to iSend! We're excited to have you on board.\n\n"
        "With iSend, you can easily submit academic requests, upload and receive documents, "
        "and track the status of each request in real time – all in one place.\n\n"
        "If you ever need help, our smart assistant is here to guide you step-by-step.\n\n"
        "Let’s make your academic life easier, more organized, and stress-free 🎓\n\n"
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
    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    msg = None
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            if user.is_lecturer and not user.is_approved:
                msg = "Lecturer account is awaiting admin approval."
            else:
                login(request, user)

                # Send login email
                send_mail(
                    subject='🔐 New Login Detected',
                    message=f'Hi {user.username}, you have just logged into your ISEND account.',
                    from_email=None,
                    recipient_list=[user.email],
                    fail_silently=False,
                )

                if user.is_student:
                    return redirect('blog-home')
                elif user.is_lecturer:
                    return redirect('lecturer_dashboard')
                elif user.is_superuser:
                    return redirect('adminpage')
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



def is_approved_lecturer(user):
    return user.is_authenticated and user.is_lecturer and user.is_approved

@login_required
@user_passes_test(is_approved_lecturer)
def lecturer_dashboard(request):
    return render(request, 'users/lecturer_dashboard.html')  # or 'account/lecturer_dashboard.html'
@requires_csrf_token
def csrf_failure(request, reason=""):
    return render(request, 'users/csrf_failure.html', status=403, context={'reason': reason})

from blog.models import AcademicRequest
from django.shortcuts import get_object_or_404, redirect

def update_request_status(request, request_id):
    if request.method == "POST" and request.user.lecturerprofile:
        req = get_object_or_404(AcademicRequest, id=request_id)
        new_status = request.POST.get("status")
        if new_status in dict(AcademicRequest.STATUS_CHOICES).keys():
            req.status = new_status
            req.save()
    return redirect("lecturer_requests")

@login_required
def update_request_status(request, request_id):
    """
    Handle updating an academic request status
    """
    # Check if user has a lecturer profile
    try:
        lecturer_profile = request.user.lecturerprofile
    except LecturerProfile.DoesNotExist:
        # Handle case where user is not a lecturer
        return redirect('home')  # Redirect to appropriate page
    
    # Get the academic request
    academic_request = get_object_or_404(AcademicRequest, id=request_id)
    
    if request.method == 'POST':
        # Get form data
        status = request.POST.get('status')
        lecturer_note = request.POST.get('lecturer_note')
        update_deadline = request.POST.get('update_deadline')
        
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
        
        # Add success message if messages framework is enabled
        try:
            from django.contrib import messages
            messages.success(request, 'הבקשה עודכנה בהצלחה')
        except ImportError:
            pass
    
    # Redirect back to dashboard
    return redirect('lecturer_dashboard')
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
from django.db import models 
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from .models import AcademicRequest, LecturerProfile
from django.contrib.auth.models import User

@login_required
def lecturer_dashboard(request):
    """
    Display the lecturer dashboard with academic requests and handle request updates.
    """
    # Check if user has a lecturer profile
    try:
        lecturer_profile = request.user.lecturerprofile
    except LecturerProfile.DoesNotExist:
        # Handle case where user is not a lecturer
        return redirect('home')  # Redirect to appropriate page
    
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
    
    # Get all academic requests
    academic_requests = AcademicRequest.objects.all().order_by('-created_at')
    
    # Paginate requests
    paginator = Paginator(academic_requests, 10)  # 10 items per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get requests by status
    pending_requests = AcademicRequest.objects.filter(status='pending')
    in_progress_requests = AcademicRequest.objects.filter(status='in_progress')
    need_update_requests = AcademicRequest.objects.filter(status='need_update')
    approved_requests = AcademicRequest.objects.filter(status='approved')
    rejected_requests = AcademicRequest.objects.filter(status='rejected')
    
    # Get recent requests (last 5)
    recent_requests = AcademicRequest.objects.all().order_by('-created_at')[:5]
    
    # Get upcoming deadlines (requests with deadlines in the next 7 days)
    today = timezone.now()
    week_later = today + timedelta(days=7)
    
    # First query all requests with deadlines
    deadline_requests = (
        AcademicRequest.objects
        .filter(update_deadline__isnull=False)
        .order_by('update_deadline')
    )
    
    # Then filter in Python for those that are past deadline or within a week
    upcoming_deadlines = []
    for academic_req in deadline_requests:  # Renamed from 'request' to 'academic_req'
        if academic_req.is_past_deadline() or academic_req.update_deadline <= week_later:
            upcoming_deadlines.append(academic_req)
            if len(upcoming_deadlines) >= 5:
                break
    
    
    context = {
        'lecturer_profile': lecturer_profile,
        'academic_requests': page_obj,
        'pending_requests': pending_requests,
        'in_progress_requests': in_progress_requests,
        'need_update_requests': need_update_requests,
        'approved_requests': approved_requests,
        'rejected_requests': rejected_requests,
        'pending_requests_count': pending_requests.count(),
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