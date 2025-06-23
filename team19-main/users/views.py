from datetime import timedelta
from blog.models import AcademicRequest, ScheduleRequest, PersonalRequest
from .models import Subject  # Subject model from users app

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Count, Q
from django.http import JsonResponse, HttpResponse
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

## Replace your register function in users/views.py with this clean version:

# FIXED REGISTER FUNCTION - Replace in users/views.py
# Add this debug function to your users/views.py to understand request handling

@login_required
def debug_request_handlers(request):
    """Debug function to show which requests are handled by whom"""
    if not request.user.is_superuser and not request.user.is_lecturer:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Define handler rules
    LECTURER_ACADEMIC_TYPES = ['academic_appeal', 'exam_review']
    SECRETARY_ACADEMIC_TYPES = ['enrollment_confirmation']
    
    LECTURER_PERSONAL_TYPES = ['recommendation_letter']
    SECRETARY_PERSONAL_TYPES = [
        'personal_details_update', 'certificates_confirmations',
        'scholarships_financial_aid', 'academic_status_change',
        'general_manager_inquiry'
    ]
    
    # ALL schedule requests are handled by secretaries
    SCHEDULE_TYPES = ['schedule_change', 'extension_request', 'special_exam_date', 'approved_absence']
    
    debug_info = {
        'handler_rules': {
            'lecturer_handles': {
                'academic': LECTURER_ACADEMIC_TYPES,
                'personal': LECTURER_PERSONAL_TYPES,
                'schedule': []  # Lecturers don't handle schedule requests
            },
            'secretary_handles': {
                'academic': SECRETARY_ACADEMIC_TYPES,
                'personal': SECRETARY_PERSONAL_TYPES,
                'schedule': SCHEDULE_TYPES  # All schedule requests
            }
        },
        'current_requests': {
            'academic': [],
            'personal': [],
            'schedule': []
        }
    }
    
    # Get current requests in the department
    department = request.user.department
    
    # Check Academic requests
    academic_requests = AcademicRequest.objects.filter(student__department=department)
    for req in academic_requests:
        handler = 'lecturer' if req.request_type in LECTURER_ACADEMIC_TYPES else 'secretary'
        debug_info['current_requests']['academic'].append({
            'id': req.id,
            'type': req.request_type,
            'status': req.status,
            'student': req.student.username,
            'handler': handler,
            'lecturer_can_update': handler == 'lecturer'
        })
    
    # Check Personal requests
    personal_requests = PersonalRequest.objects.filter(student__department=department)
    for req in personal_requests:
        handler = 'lecturer' if req.request_type in LECTURER_PERSONAL_TYPES else 'secretary'
        debug_info['current_requests']['personal'].append({
            'id': req.id,
            'type': req.request_type,
            'status': req.status,
            'student': req.student.username,
            'handler': handler,
            'lecturer_can_update': handler == 'lecturer'
        })
    
    # Check Schedule requests
    schedule_requests = ScheduleRequest.objects.filter(student__department=department)
    for req in schedule_requests:
        debug_info['current_requests']['schedule'].append({
            'id': req.id,
            'type': req.request_type,
            'status': req.status,
            'student': req.student.username,
            'handler': 'secretary',  # ALL schedule requests are secretary-only
            'lecturer_can_update': False  # Lecturers CANNOT update schedule requests
        })
    
    # Summary
    debug_info['summary'] = {
        'total_academic': len(debug_info['current_requests']['academic']),
        'lecturer_academic': len([r for r in debug_info['current_requests']['academic'] if r['lecturer_can_update']]),
        'secretary_academic': len([r for r in debug_info['current_requests']['academic'] if not r['lecturer_can_update']]),
        
        'total_personal': len(debug_info['current_requests']['personal']),
        'lecturer_personal': len([r for r in debug_info['current_requests']['personal'] if r['lecturer_can_update']]),
        'secretary_personal': len([r for r in debug_info['current_requests']['personal'] if not r['lecturer_can_update']]),
        
        'total_schedule': len(debug_info['current_requests']['schedule']),
        'lecturer_schedule': 0,  # Always 0 - lecturers don't handle schedule
        'secretary_schedule': len(debug_info['current_requests']['schedule']),
    }
    
    return JsonResponse(debug_info, ensure_ascii=False, json_dumps_params={'indent': 2})

# Add this URL to test: path('debug-handlers/', views.debug_request_handlers, name='debug_handlers'),
def register(request):
    msg = None
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.department = form.cleaned_data.get('department')
            user.year = form.cleaned_data.get('year') 
            user.save()
            if user.is_lecturer:
                # Create lecturer profile first
                lecturer_profile, created = LecturerProfile.objects.get_or_create(
                    user=user,
                    defaults={'subject': ''}
                )
                
                courses_json = form.cleaned_data.get('courses')
                print(f"🔧 Creating courses for lecturer: {user.username}")
                print(f"📝 User department: {user.department}")
                print(f"📚 Courses JSON: {courses_json}")
                
                if courses_json:
                    try:
                        courses_list = json.loads(courses_json)
                        print(f"✅ Parsed courses: {courses_list}")
                        
                        # Map English departments to Hebrew
                        dept_mapping = {
                            'sw_engineering': 'הנדסת תוכנה',
                            'computer_science': 'מדעי המחשב',
                            'electronic_engineering': 'הנדסת אלקטרוניקה'
                        }
                        
                        # Get the correct department name
                        dept_name = dept_mapping.get(user.department, user.department)
                        print(f"🏢 Department mapped to: {dept_name}")
                        
                        created_subjects = []
                        for course_name in courses_list:
                            course_name = course_name.strip()
                            if course_name:
                                # Create subject with the mapped department name
                                subject, created = Subject.objects.get_or_create(
                                    name=course_name,
                                    lecturer=user,
                                    defaults={
                                        'department': dept_name
                                    }
                                )
                                created_subjects.append(subject)
                                print(f"{'✅ Created' if created else '📚 Exists'}: {subject.name} - {subject.department}")
                        
                        # Update lecturer profile with subjects
                        subject_names = [s.name for s in created_subjects]
                        lecturer_profile.subject = ', '.join(subject_names)
                        lecturer_profile.save()
                        
                        print(f"🎉 Total subjects for {user.username}: {len(created_subjects)}")
                        print(f"📋 Subject names: {subject_names}")
                        
                        # Double-check by querying the database
                        db_subjects = Subject.objects.filter(lecturer=user)
                        print(f"✅ Verified - Subjects in database: {list(db_subjects.values_list('name', flat=True))}")
                        
                    except (json.JSONDecodeError, TypeError) as e:
                        print(f"❌ Error parsing courses: {e}")
                        import traceback
                        traceback.print_exc()
                else:
                    print("⚠️  No courses data found in form")
            
            # Send welcome email
            try:
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
                    fail_silently=True,
                )
            except Exception as e:
                print(f"📧 Email sending failed: {e}")

            if user.is_student:
                login(request, user)
                return redirect('blog-home')
            elif user.is_lecturer:
                msg = "Lecturer account created successfully! Please login to access your dashboard."
                return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form, 'msg': msg})

# ALSO ADD THIS DEBUGGING FUNCTION TO CHECK REGISTRATION:

def debug_lecturer_registration(request):
    """Debug function to check if lecturer subjects are being saved"""
    if request.user.is_superuser:
        print("🔍 DEBUGGING LECTURER REGISTRATION")
        print("=" * 40)
        
        lecturers = User.objects.filter(is_lecturer=True)
        for lecturer in lecturers:
            print(f"\n👨‍🏫 Lecturer: {lecturer.username}")
            print(f"   🏢 Department: {lecturer.department}")
            
            # Check lecturer profile
            try:
                profile = lecturer.lecturerprofile
                print(f"   📋 Profile subjects: {profile.subject}")
            except LecturerProfile.DoesNotExist:
                print(f"   ❌ No lecturer profile found!")
            
            # Check actual subjects
            subjects = Subject.objects.filter(lecturer=lecturer)
            print(f"   📚 Database subjects: {list(subjects.values_list('name', flat=True))}")
            print(f"   📊 Total subjects: {subjects.count()}")
        
        return JsonResponse({'status': 'debug_complete'})
    else:
        return JsonResponse({'status': 'unauthorized'})

# ADD THIS URL TO YOUR urls.py FOR DEBUGGING:
# path('debug-lecturers/', views.debug_lecturer_registration, name='debug_lecturers'),
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
                    return redirect('secretary_dashboard')
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
    # Get chat history for the current user
    history = ChatHistory.objects.filter(username=request.user.username).order_by('-timestamp')
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
        'p_form': p_form,
        'history': history
    }

    return render(request, 'users/profile.html', context)

from dotenv import load_dotenv
from pathlib import Path
from openai import OpenAI
import os
from blog.models import ChatHistory
from django.contrib.auth import update_session_auth_hash

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@requires_csrf_token
def csrf_failure(request, reason=""):
    return render(request, 'users/csrf_failure.html', {'reason': reason}, status=403)

# This version follows the same pattern as the working secretary version


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
# Replace BOTH the lecturer_dashboard AND update_request_status functions in users/views.py

@login_required
def lecturer_dashboard(request):
    """Lecturer dashboard - FIXED VERSION showing only lecturer-handled requests"""
    # Check if user is a lecturer
    if not request.user.is_lecturer:
        messages.error(request, 'הגישה מותרת למרצים בלבד.')
        return redirect('blog-home')
    
    # IMPORTANT: Define EXACTLY which request types lecturers handle
    LECTURER_ACADEMIC_TYPES = [
        'academic_appeal',  # ערעורים אקדמיים
        'exam_review',      # בקשות לבדיקת מבחנים
    ]
    
    LECTURER_PERSONAL_TYPES = [
        'recommendation_letter',  # בקשה למכתבי המלצה
    ]
    
    # NOTE: Lecturers do NOT handle schedule requests - only secretaries do
    
    print(f"🎓 Lecturer Dashboard - User: {request.user.username}, Department: {request.user.department}")
    
    # Get academic requests ONLY for lecturer-handled types
    academic_requests = AcademicRequest.objects.filter(
        student__department=request.user.department,
        request_type__in=LECTURER_ACADEMIC_TYPES
    ).select_related('student').order_by('-created_at')
    
    print(f"📚 Academic requests (lecturer types): {academic_requests.count()}")
    for req in academic_requests:
        print(f"  - Academic ID: {req.id}, Type: {req.request_type}, Status: {req.status}")
    
    # Get personal requests ONLY for lecturer-handled types
    personal_requests = PersonalRequest.objects.filter(
        student__department=request.user.department,
        request_type__in=LECTURER_PERSONAL_TYPES
    ).select_related('student').order_by('-created_at')
    
    print(f"👤 Personal requests (lecturer types): {personal_requests.count()}")
    for req in personal_requests:
        print(f"  - Personal ID: {req.id}, Type: {req.request_type}, Status: {req.status}")
    
    # Combine all lecturer-handled requests
    all_requests = list(academic_requests) + list(personal_requests)
    all_requests.sort(key=lambda x: x.created_at, reverse=True)
    
    print(f"📊 Total lecturer requests: {len(all_requests)}")
    
    # Filter by status if provided
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        filtered_requests = [req for req in all_requests if req.status == status_filter]
    else:
        filtered_requests = all_requests
    
    # Get statistics
    stats = {
        'total': len(all_requests),
        'pending': len([req for req in all_requests if req.status == 'pending']),
        'in_progress': len([req for req in all_requests if req.status == 'in_progress']),
        'need_update': len([req for req in all_requests if req.status == 'need_update']),
        'approved': len([req for req in all_requests if req.status == 'approved']),
        'rejected': len([req for req in all_requests if req.status == 'rejected']),
        'academic_total': academic_requests.count(),
        'personal_total': personal_requests.count(),
        'schedule_total': 0,  # Lecturers don't handle schedule requests
    }
    
    context = {
        'all_requests': all_requests,
        'filtered_requests': filtered_requests,
        'stats': stats,
        'status_filter': status_filter,
        'department_display': request.user.department,
        'academic_requests': academic_requests,
        'personal_requests': personal_requests,
        'schedule_requests': [],  # Empty - lecturers don't handle these
        'lecturer_handled_types': {
            'academic': LECTURER_ACADEMIC_TYPES,
            'personal': LECTURER_PERSONAL_TYPES,
        },
        'note': 'Lecturers only handle: Academic Appeals, Exam Reviews, and Recommendation Letters'
    }
    
    return render(request, 'users/lecturer_dashboard.html', context)


import os
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth.decorators import login_required

@login_required
def update_request_status(request, request_id):
    """Update request status for any request type (academic, schedule, or personal) with file upload support"""
    if request.method == 'POST':
        try:
            new_status = request.POST.get('status')
            request_type = request.POST.get('request_type', '').lower()  # Must be sent explicitly from frontend
            secretary_note = request.POST.get('secretary_note', '')
            lecturer_note = request.POST.get('lecturer_note', '')
            update_deadline = request.POST.get('update_deadline')

            # Handle file uploads
            lecturer_file = request.FILES.get('lecturer_file')
            secretary_file = request.FILES.get('secretary_file')

            print(f"🔄 DEBUGGING: Updating request status for ID: {request_id}")
            print(f"📊 DEBUGGING: New status: {new_status}")
            print(f"📋 DEBUGGING: Request type hint: {request_type}")
            print(f"📝 DEBUGGING: Secretary note: {secretary_note}")
            print(f"📝 DEBUGGING: Lecturer note: {lecturer_note}")
            print(f"📅 DEBUGGING: Update deadline: {update_deadline}")
            print(f"📎 DEBUGGING: Lecturer file: {lecturer_file.name if lecturer_file else 'None'}")
            print(f"📎 DEBUGGING: Secretary file: {secretary_file.name if secretary_file else 'None'}")

            # Validate status
            valid_statuses = ['pending', 'in_progress', 'need_update', 'approved', 'rejected']
            if new_status not in valid_statuses:
                print(f"❌ DEBUGGING: Invalid status: {new_status}")
                return JsonResponse({'success': False, 'message': 'סטטוס לא תקין'})

            # Import models here (adjust import path as needed)

            # Pick model based on request_type
            request_obj = None
            model_name = ""

            if request_type == 'academic':
                request_obj = AcademicRequest.objects.get(id=request_id)
                model_name = "Academic"
            elif request_type == 'schedule':
                request_obj = ScheduleRequest.objects.get(id=request_id)
                model_name = "Schedule"
            elif request_type == 'personal':
                request_obj = PersonalRequest.objects.get(id=request_id)
                model_name = "Personal"
            else:
                return JsonResponse({'success': False, 'message': 'סוג בקשה לא תקין'})

            # Determine user role
            user_profile = getattr(request.user, 'profile', None)
            is_lecturer = hasattr(request.user, 'lecturerprofile')
            is_secretary = hasattr(request.user, 'secretaryprofile') or (user_profile and user_profile.role == 'secretary')

            old_status = request_obj.status
            request_obj.status = new_status

            # Update notes
            if is_lecturer and lecturer_note:
                if hasattr(request_obj, 'lecturer_note'):
                    request_obj.lecturer_note = lecturer_note
                    print(f"📝 DEBUGGING: Updated lecturer note: {lecturer_note[:50]}...")
                else:
                    print(f"⚠️ DEBUGGING: No lecturer_note field in {model_name} model")

            if is_secretary and secretary_note:
                if hasattr(request_obj, 'secretary_note'):
                    request_obj.secretary_note = secretary_note
                    print(f"📝 DEBUGGING: Updated secretary note: {secretary_note[:50]}...")
                elif hasattr(request_obj, 'lecturer_note'):
                    request_obj.lecturer_note = secretary_note
                    print(f"📝 DEBUGGING: Updated note (via lecturer_note field): {secretary_note[:50]}...")
                else:
                    print(f"⚠️ DEBUGGING: No note field found for {model_name} request")

            # Validate and save lecturer file
            if is_lecturer and lecturer_file:
                if hasattr(request_obj, 'lecturer_file'):
                    if lecturer_file.size > 10 * 1024 * 1024:
                        return JsonResponse({'success': False, 'message': 'גודל הקובץ חורג מ-10MB'})
                    allowed_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.jpg', '.jpeg', '.png']
                    ext = os.path.splitext(lecturer_file.name)[1].lower()
                    if ext not in allowed_extensions:
                        return JsonResponse({'success': False, 'message': 'סוג קובץ לא נתמך'})
                    request_obj.lecturer_file = lecturer_file
                    request_obj.lecturer_file_name = lecturer_file.name
                    request_obj.lecturer_file_uploaded_at = timezone.now()
                    print(f"📎 DEBUGGING: Uploaded lecturer file: {lecturer_file.name}")
                else:
                    print(f"⚠️ DEBUGGING: No lecturer_file field in {model_name} model")

            # Validate and save secretary file
            if is_secretary and secretary_file:
                if hasattr(request_obj, 'secretary_file'):
                    if secretary_file.size > 10 * 1024 * 1024:
                        return JsonResponse({'success': False, 'message': 'גודל הקובץ חורג מ-10MB'})
                    allowed_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.jpg', '.jpeg', '.png']
                    ext = os.path.splitext(secretary_file.name)[1].lower()
                    if ext not in allowed_extensions:
                        return JsonResponse({'success': False, 'message': 'סוג קובץ לא נתמך'})
                    request_obj.secretary_file = secretary_file
                    request_obj.secretary_file_name = secretary_file.name
                    request_obj.secretary_file_uploaded_at = timezone.now()
                    print(f"📎 DEBUGGING: Uploaded secretary file: {secretary_file.name}")
                else:
                    print(f"⚠️ DEBUGGING: No secretary_file field in {model_name} model")

            # Handle update deadline for need_update status
            if new_status == 'need_update' and update_deadline:
                if hasattr(request_obj, 'update_deadline'):
                    from datetime import datetime
                    try:
                        deadline_date = datetime.strptime(update_deadline, '%Y-%m-%d').date()
                        request_obj.update_deadline = deadline_date
                        print(f"📅 DEBUGGING: Set update deadline to: {deadline_date}")
                    except ValueError as e:
                        print(f"❌ DEBUGGING: Invalid date format: {update_deadline}, error: {e}")
            elif new_status != 'need_update' and hasattr(request_obj, 'update_deadline'):
                request_obj.update_deadline = None

            request_obj.save()
            print(f"✅ DEBUGGING: {model_name} request {request_id} status updated: {old_status} -> {new_status}")

            # Re-fetch to verify save
            re_fetched_obj = None
            if model_name == "Academic":
                re_fetched_obj = AcademicRequest.objects.get(id=request_id)
            elif model_name == "Schedule":
                re_fetched_obj = ScheduleRequest.objects.get(id=request_id)
            elif model_name == "Personal":
                re_fetched_obj = PersonalRequest.objects.get(id=request_id)

            if re_fetched_obj:
                print(f"🔍 DEBUGGING: Re-fetched {model_name} request {request_id} status AFTER save: {re_fetched_obj.status}")
            else:
                print(f"❌ DEBUGGING: Failed to re-fetch {model_name} request {request_id} after save.")

            return JsonResponse({
                'success': True,
                'message': f'סטטוס עודכן בהצלחה ({model_name})',
                'request_type': model_name.lower(),
                'old_status': old_status,
                'new_status': new_status,
                'file_uploaded': bool(lecturer_file or secretary_file),
                'lecturer_file_uploaded': bool(lecturer_file),
                'secretary_file_uploaded': bool(secretary_file)
            })

        except Exception as e:
            print(f"❌ DEBUGGING: General error updating request status: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'message': f'שגיאה: {str(e)}'})

    print(f"⚠️ DEBUGGING: Invalid request method: {request.method}")
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
def get_request_details(request, request_id):
    """Get detailed request information for the modal - filtered by user role with file information"""
    if not request.user.is_secretary:
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    try:
        print(f"🔍 DEBUGGING: Getting request details for ID: {request_id}")
        print(f"👤 DEBUGGING: User: {request.user.username}, Role: Secretary, Department: {request.user.department}")
        
        # Define which request types are handled by secretaries vs lecturers
        secretary_academic_types = [
            'enrollment_confirmation',  # אישורי רישום או ציונים
            # Add other secretary-specific academic types here if any
        ]
        
        lecturer_academic_types = [
            'academic_appeal',  # ערעורים אקדמיים
            'exam_review',      # בקשות לבדיקת מבחנים
        ]
        
        secretary_personal_types = [
            'personal_details_update',        # עדכון פרטים אישיים
            'certificates_confirmations',     # בקשת תעודות ואישורים
            'scholarships_financial_aid',     # בקשות מלגות וסיוע כלכלי
            'academic_status_change',         # בקשת שינוי סטטוס אקדמי
            'general_manager_inquiry',        # פניה כללית למנהל
        ]
        
        lecturer_personal_types = [
            'recommendation_letter',          # בקשה למכתבי המלצה (handled by lecturers)
        ]
        
        # Try to find the request in secretary-handled models only
        request_obj = None
        model_name = ""
        
        # Check Academic requests (only secretary types)
        try:
            request_obj = AcademicRequest.objects.select_related('student').get(
                id=request_id,
                student__department=request.user.department,
                request_type__in=secretary_academic_types  # Only secretary types
            )
            model_name = "academic"
            print(f"✅ DEBUGGING: Found Secretary Academic request: {request_id}")
        except AcademicRequest.DoesNotExist:
            print(f"❌ DEBUGGING: Secretary Academic request {request_id} not found or not accessible")
        
        # Check Schedule requests (all schedule requests are handled by secretaries)
        if not request_obj:
            try:
                request_obj = ScheduleRequest.objects.select_related('student').get(
                    id=request_id,
                    student__department=request.user.department
                )
                model_name = "schedule"
                print(f"✅ DEBUGGING: Found Schedule request: {request_id}")
            except ScheduleRequest.DoesNotExist:
                print(f"❌ DEBUGGING: Schedule request {request_id} not found")
        
        # Check Personal requests (only secretary types)
        if not request_obj:
            try:
                request_obj = PersonalRequest.objects.select_related('student').get(
                    id=request_id,
                    student__department=request.user.department,
                    request_type__in=secretary_personal_types  # Only secretary types
                )
                model_name = "personal"
                print(f"✅ DEBUGGING: Found Secretary Personal request: {request_id}")
            except PersonalRequest.DoesNotExist:
                print(f"❌ DEBUGGING: Secretary Personal request {request_id} not found or not accessible")
        
        if not request_obj:
            # Check if the request exists but is lecturer-only
            lecturer_request_found = False
            
            # Check if it's a lecturer-only academic request
            try:
                lecturer_academic = AcademicRequest.objects.get(
                    id=request_id,
                    request_type__in=lecturer_academic_types
                )
                lecturer_request_found = True
                print(f"⚠️ DEBUGGING: Request {request_id} is a lecturer-only academic request: {lecturer_academic.request_type}")
            except AcademicRequest.DoesNotExist:
                pass
            
            # Check if it's a lecturer-only personal request
            if not lecturer_request_found:
                try:
                    lecturer_personal = PersonalRequest.objects.get(
                        id=request_id,
                        request_type__in=lecturer_personal_types
                    )
                    lecturer_request_found = True
                    print(f"⚠️ DEBUGGING: Request {request_id} is a lecturer-only personal request: {lecturer_personal.request_type}")
                except PersonalRequest.DoesNotExist:
                    pass
            
            if lecturer_request_found:
                return JsonResponse({
                    'success': False, 
                    'error': 'This request is handled by lecturers, not secretaries'
                })
            else:
                return JsonResponse({
                    'success': False, 
                    'error': 'Request not found'
                })
        
        # Get request type display name
        type_display_mapping = {
            # Academic request types (secretary-handled)
            'enrollment_confirmation': 'אישורי רישום או ציונים',
            # Schedule request types (all handled by secretary)
            'schedule_change': 'שינוי מערכת שעות',
            'extension_request': 'בקשות הארכת זמן',
            'special_exam_date': 'בקשה למועד מיוחד',
            'approved_absence': 'בקשת היעדרות מאושרת',
            # Personal request types (secretary-handled)
            'personal_details_update': 'עדכון פרטים אישיים',
            'certificates_confirmations': 'בקשת תעודות ואישורים',
            'scholarships_financial_aid': 'בקשות מלגות וסיוע כלכלי',
            'academic_status_change': 'בקשת שינוי סטטוס אקדמי',
            'general_manager_inquiry': 'פניה כללית למנהל',
        }
        
        # Build response data
        data = {
            'id': request_obj.id,
            'model_name': model_name,
            'student_name': request_obj.student.get_full_name() or request_obj.student.username,
            'student_id': getattr(request_obj.student, 'student_id', request_obj.student.username),
            'department': request_obj.student.department,
            'request_type_raw': request_obj.request_type,
            'request_type_display': type_display_mapping.get(request_obj.request_type, request_obj.request_type),
            'request_text': request_obj.request_text,
            'status': request_obj.status,
            'created_at': request_obj.created_at.strftime('%d/%m/%Y %H:%M'),
            'attachment': request_obj.attachment.url if request_obj.attachment else None,
            'attachment_name': request_obj.attachment.name.split('/')[-1] if request_obj.attachment else None,
        }
        
        # Add file information if fields exist
        if hasattr(request_obj, 'lecturer_file'):
            data['lecturer_file'] = {
                'exists': bool(request_obj.lecturer_file),
                'name': getattr(request_obj, 'lecturer_file_name', None),
                'uploaded_at': getattr(request_obj, 'lecturer_file_uploaded_at', None),
                'url': f'/download/{request_id}/lecturer/' if request_obj.lecturer_file else None
            }
        
        if hasattr(request_obj, 'secretary_file'):
            data['secretary_file'] = {
                'exists': bool(request_obj.secretary_file),
                'name': getattr(request_obj, 'secretary_file_name', None),
                'uploaded_at': getattr(request_obj, 'secretary_file_uploaded_at', None),
                'url': f'/download/{request_id}/secretary/' if request_obj.secretary_file else None
            }
        
        # Add subject for academic requests
        if model_name == "academic" and hasattr(request_obj, 'subject'):
            data['subject'] = request_obj.subject
        
        # Add notes based on model type
        if hasattr(request_obj, 'lecturer_note'):
            data['secretary_note'] = request_obj.lecturer_note or ''
        elif hasattr(request_obj, 'secretary_note'):
            data['secretary_note'] = request_obj.secretary_note or ''
        else:
            data['secretary_note'] = ''
        
        # Add update deadline if exists
        if hasattr(request_obj, 'update_deadline') and request_obj.update_deadline:
            data['update_deadline'] = request_obj.update_deadline.strftime('%Y-%m-%d')
            data['update_deadline_display'] = request_obj.update_deadline.strftime('%d/%m/%Y')
        else:
            data['update_deadline'] = ''
            data['update_deadline_display'] = ''
        
        print(f"✅ DEBUGGING: Returning request data for {model_name} request {request_id}")
        return JsonResponse(data)
        
    except Exception as e:
        print(f"❌ DEBUGGING: Error getting request details: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def download_file(request, request_id, file_type):
    """Download uploaded files (lecturer or secretary files)"""
    try:
        # Get the request object from any model
        request_obj = None
        try:
            request_obj = AcademicRequest.objects.get(id=request_id)
        except AcademicRequest.DoesNotExist:
            try:
                request_obj = PersonalRequest.objects.get(id=request_id)
            except PersonalRequest.DoesNotExist:
                try:
                    request_obj = ScheduleRequest.objects.get(id=request_id)
                except ScheduleRequest.DoesNotExist:
                    return HttpResponse('Request not found', status=404)
        
        # Security check - ensure user has access to this request
        user_profile = getattr(request.user, 'profile', None)
        is_student = user_profile and user_profile.role == 'student'
        is_lecturer = hasattr(request.user, 'lecturerprofile')
        is_secretary = hasattr(request.user, 'secretaryprofile') or (user_profile and user_profile.role == 'secretary')
        
        # Students can only download files for their own requests
        if is_student and request_obj.student != request.user:
            return HttpResponse('Access denied', status=403)
        
        # Get the appropriate file
        file_field = None
        file_name = None
        
        if file_type == 'lecturer' and hasattr(request_obj, 'lecturer_file'):
            file_field = request_obj.lecturer_file
            file_name = request_obj.lecturer_file_name
        elif file_type == 'secretary' and hasattr(request_obj, 'secretary_file'):
            file_field = request_obj.secretary_file
            file_name = request_obj.secretary_file_name
        
        if not file_field:
            return HttpResponse('File not found', status=404)
        
        # Serve the file
        response = HttpResponse(file_field.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{file_name or os.path.basename(file_field.name)}"'
        return response
        
    except Exception as e:
        print(f"❌ Error downloading file: {str(e)}")
        return HttpResponse(f'Error downloading file: {str(e)}', status=500)
@login_required
def lecturer_get_request_details(request, request_id):
    """Get detailed request information for the lecturer modal - filtered by lecturer role"""
    if not request.user.is_lecturer:
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    try:
        print(f"🔍 DEBUGGING: Getting lecturer request details for ID: {request_id}")
        print(f"👤 DEBUGGING: User: {request.user.username}, Role: Lecturer, Department: {request.user.department}")
        
        # Define which request types are handled by lecturers vs secretaries
        LECTURER_ACADEMIC_TYPES = [
            'academic_appeal',  # ערעורים אקדמיים
            'exam_review',      # בקשות לבדיקת מבחנים
        ]
        
        SECRETARY_ACADEMIC_TYPES = [
            'enrollment_confirmation',  # אישורי רישום או ציונים
        ]
        
        LECTURER_PERSONAL_TYPES = [
            'recommendation_letter',  # בקשה למכתבי המלצה
        ]
        
        SECRETARY_PERSONAL_TYPES = [
            'personal_details_update',        # עדכון פרטים אישיים
            'certificates_confirmations',     # בקשת תעודות ואישורים
            'scholarships_financial_aid',     # בקשות מלגות וסיוע כלכלי
            'academic_status_change',         # בקשת שינוי סטטוס אקדמי
            'general_manager_inquiry',        # פניה כללית למנהל
        ]
        
        # Try to find the request in lecturer-handled models only
        request_obj = None
        model_name = ""
        
        # Check Academic requests (only lecturer types)
        try:
            request_obj = AcademicRequest.objects.select_related('student').get(
                id=request_id,
                student__department=request.user.department,
                request_type__in=LECTURER_ACADEMIC_TYPES  # Only lecturer types
            )
            model_name = "academic"
            print(f"✅ DEBUGGING: Found Lecturer Academic request: {request_id}")
        except AcademicRequest.DoesNotExist:
            print(f"❌ DEBUGGING: Lecturer Academic request {request_id} not found or not accessible")
        
        # Check Personal requests (only lecturer types)
        if not request_obj:
            try:
                request_obj = PersonalRequest.objects.select_related('student').get(
                    id=request_id,
                    student__department=request.user.department,
                    request_type__in=LECTURER_PERSONAL_TYPES  # Only lecturer types
                )
                model_name = "personal"
                print(f"✅ DEBUGGING: Found Lecturer Personal request: {request_id}")
            except PersonalRequest.DoesNotExist:
                print(f"❌ DEBUGGING: Lecturer Personal request {request_id} not found or not accessible")
        
        if not request_obj:
            # Check if the request exists but is secretary-only
            secretary_request_found = False
            secretary_request_type = ""
            
            # Check if it's a secretary-only academic request
            try:
                secretary_academic = AcademicRequest.objects.get(
                    id=request_id,
                    student__department=request.user.department,
                    request_type__in=SECRETARY_ACADEMIC_TYPES
                )
                secretary_request_found = True
                secretary_request_type = f"Academic - {secretary_academic.request_type}"
                print(f"⚠️ DEBUGGING: Request {request_id} is a secretary-only academic request: {secretary_academic.request_type}")
            except AcademicRequest.DoesNotExist:
                pass
            
            # Check if it's a secretary-only personal request
            if not secretary_request_found:
                try:
                    secretary_personal = PersonalRequest.objects.get(
                        id=request_id,
                        student__department=request.user.department,
                        request_type__in=SECRETARY_PERSONAL_TYPES
                    )
                    secretary_request_found = True
                    secretary_request_type = f"Personal - {secretary_personal.request_type}"
                    print(f"⚠️ DEBUGGING: Request {request_id} is a secretary-only personal request: {secretary_personal.request_type}")
                except PersonalRequest.DoesNotExist:
                    pass
            
            # Check if it's a schedule request (all handled by secretary)
            if not secretary_request_found:
                try:
                    secretary_schedule = ScheduleRequest.objects.get(
                        id=request_id,
                        student__department=request.user.department
                    )
                    secretary_request_found = True
                    secretary_request_type = f"Schedule - {secretary_schedule.request_type}"
                    print(f"⚠️ DEBUGGING: Request {request_id} is a secretary-only schedule request: {secretary_schedule.request_type}")
                except ScheduleRequest.DoesNotExist:
                    pass
            
            if secretary_request_found:
                return JsonResponse({
                    'success': False, 
                    'error': f'This request ({secretary_request_type}) is handled by secretaries, not lecturers',
                    'is_secretary_request': True
                })
            else:
                return JsonResponse({
                    'success': False, 
                    'error': 'Request not found or not accessible',
                    'is_secretary_request': False
                })
        
        # Get request type display name
        type_display_mapping = {
            # Academic request types (lecturer-handled)
            'academic_appeal': 'ערעורים אקדמיים',
            'exam_review': 'בקשות לבדיקת מבחנים',
            # Personal request types (lecturer-handled)
            'recommendation_letter': 'בקשה למכתבי המלצה',
        }
        
        # Build response data
        data = {
            'id': request_obj.id,
            'model_name': model_name,
            'student_name': request_obj.student.get_full_name() or request_obj.student.username,
            'student_id': getattr(request_obj.student, 'student_id', request_obj.student.username),
            'department': request_obj.student.department,
            'request_type_raw': request_obj.request_type,
            'request_type_display': type_display_mapping.get(request_obj.request_type, request_obj.request_type),
            'request_text': request_obj.request_text,
            'status': request_obj.status,
            'created_at': request_obj.created_at.strftime('%d/%m/%Y %H:%M'),
            'attachment': request_obj.attachment.url if request_obj.attachment else None,
            'attachment_name': request_obj.attachment.name.split('/')[-1] if request_obj.attachment else None,
        }
        
        # Add subject for academic requests
        if model_name == "academic" and hasattr(request_obj, 'subject'):
            data['subject'] = request_obj.subject
        
        # Add notes based on model type
        if hasattr(request_obj, 'lecturer_note'):
            data['lecturer_note'] = request_obj.lecturer_note or ''
        elif hasattr(request_obj, 'secretary_note'):
            data['lecturer_note'] = request_obj.secretary_note or ''
        else:
            data['lecturer_note'] = ''
        
        # Add update deadline if exists
        if hasattr(request_obj, 'update_deadline') and request_obj.update_deadline:
            data['update_deadline'] = request_obj.update_deadline.strftime('%Y-%m-%d')
            data['update_deadline_display'] = request_obj.update_deadline.strftime('%d/%m/%Y')
        else:
            data['update_deadline'] = ''
            data['update_deadline_display'] = ''
        
        print(f"✅ DEBUGGING: Returning lecturer request data for {model_name} request {request_id}")
        return JsonResponse(data)
        
    except Exception as e:
        print(f"❌ DEBUGGING: Error getting lecturer request details: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)})





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




from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.conf import settings
from .forms import PasswordManagementForm
from django.contrib.auth import get_user_model
from django.http import HttpResponseForbidden
from django.contrib.auth.models import User
from django.shortcuts import render
User = get_user_model()

@login_required
@user_passes_test(lambda u: u.is_secretary)

# Add this view to your views.py file

@login_required
def secretary_user_management(request):
    """Secretary user management - only users from the same department"""
    # Check if user is a secretary
    if not request.user.is_secretary:
        messages.error(request, 'הגישה מותרת למזכירות בלבד.')
        return redirect('blog-home')
    
    # Get secretary's department
    secretary_department = request.user.department
    
    # Filter users by department (only students and lecturers)
    users = User.objects.filter(
        department=secretary_department
    ).filter(
        Q(is_student=True) | Q(is_lecturer=True)
    ).exclude(
        id=request.user.id  # Exclude the secretary themselves
    ).order_by('-date_joined')
    
    # Debug logging
    print(f"Secretary: {request.user.username}, Department: {secretary_department}")
    print(f"Users found in department: {users.count()}")
    
    # Statistics
    students_count = users.filter(is_student=True).count()
    lecturers_count = users.filter(is_lecturer=True).count()
    active_count = users.filter(is_active=True).count()
    
    context = {
        'users': users,
        'secretary_department': secretary_department,
        'students_count': students_count,
        'lecturers_count': lecturers_count,
        'active_count': active_count,
        'total_count': users.count(),
    }
    
    return render(request, 'blog/secretary_user_management.html', context)

@login_required
def secretary_delete_user(request, user_id):
    """Delete a user - only if secretary and user are in same department"""
    if not request.user.is_secretary:
        messages.error(request, 'הגישה מותרת למזכירות בלבד.')
        return redirect('blog-home')
    
    user_to_delete = get_object_or_404(User, id=user_id)
    
    # Check if user is in the same department as secretary
    if user_to_delete.department != request.user.department:
        messages.error(request, 'אין לך הרשאה למחוק משתמש ממחלקה אחרת.')
        return redirect('secretary_user_management')
    
    # Prevent deleting other secretaries or admins
    if user_to_delete.is_secretary or user_to_delete.is_superuser or user_to_delete.is_staff:
        messages.error(request, 'אין אפשרות למחוק מזכירים או מנהלי מערכת.')
        return redirect('secretary_user_management')
    
    if request.method == 'POST':
        username = user_to_delete.get_full_name() or user_to_delete.username
        user_to_delete.delete()
        messages.success(request, f'המשתמש "{username}" נמחק בהצלחה.')
        return redirect('secretary_user_management')
    
    return redirect('secretary_user_management')
def secretary_user_list(request):
    users = User.objects.exclude(is_superuser=True).exclude(is_staff=True).exclude(is_secretary=True)
    return render(request, 'users/secretary_user_list.html', {'users': users})


def change_password_direct(request):
    """Direct access to password change form"""
    return password_management(request, direct_access=True)

def password_management(request, direct_access=False):
    # If coming from profile page, go straight to password change form
    if request.user.is_authenticated and direct_access:
        request.session['password_stage'] = 'change'
    
    stage = request.session.get('password_stage', 'change' if request.user.is_authenticated else 'request_code')
    
    if request.method == 'POST':
        form = PasswordManagementForm(
            user=request.user if request.user.is_authenticated else None,
            stage=stage,
            data=request.POST
        )
        
        if form.is_valid():
            if stage == 'change' and request.user.is_authenticated:
                # Handle password change for logged-in users
                user = form.save()
                update_session_auth_hash(request, user)  # Keep user logged in
                
                # Send email notification
                send_mail(
                    'Password Changed Successfully',
                    f'Hello {user.username},\n\nYour password has been successfully changed.',
                    settings.EMAIL_HOST_USER,
                    [user.email],
                    fail_silently=False,
                )
                
                messages.success(request, 'Your password was successfully updated!')
                return redirect('password_management')
            
            elif stage == 'request_code':
                # Handle password reset request
                email = form.cleaned_data['email']
                try:
                    user = User.objects.get(email=email)
                    
                    # Generate a simple 6-digit code
                    reset_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
                    
                    # Store in session (temporary storage)
                    request.session['reset_code'] = reset_code
                    request.session['reset_user_id'] = user.id
                    request.session['password_stage'] = 'reset'  # Go directly to reset stage
                    
                    # Send email with code
                    try:
                        send_mail(
                            'Your Password Reset Code - SCE System',
                            f'Hello {user.username},\n\n'
                            f'Your verification code is: {reset_code}\n\n'
                            'This code will expire in 15 minutes.\n\n'
                            'If you didn\'t request this, please ignore this email.',
                            settings.EMAIL_HOST_USER,
                            [email],
                            fail_silently=False,
                        )
                        messages.info(request, 'Verification code sent to your email.')
                    except Exception as e:
                        messages.error(request, 'Failed to send email. Please try again later.')
                        print(f"Email sending error: {e}")  # For debugging
                        return redirect('password_management')
                    
                    return redirect('password_management')
                
                except User.DoesNotExist:
                    messages.info(request, 'If an account exists with this email, you will receive a verification code.')
                    return redirect('password_management')
            
            elif stage == 'reset':
                # Handle password reset with verification code
                user_id = request.session.get('reset_user_id')
                submitted_code = form.cleaned_data.get('code')
                stored_code = request.session.get('reset_code')
                
                if not user_id or not stored_code:
                    messages.error(request, 'Please start the reset process again.')
                    return redirect('forgot_password')
                
                # Verify the code
                if submitted_code != stored_code:
                    messages.error(request, 'Invalid verification code.')
                    return redirect('password_management')
                
                try:
                    user = User.objects.get(id=user_id)
                    new_password = form.cleaned_data['new_password1']
                    user.set_password(new_password)
                    user.save()
                    
                    # Clean up session
                    del request.session['password_stage']
                    del request.session['reset_user_id']
                    del request.session['reset_code']
                    
                    # Send confirmation email
                    send_mail(
                        'Password Reset Successfully',
                        f'Hello {user.username},\n\nYour password has been successfully reset.',
                        settings.EMAIL_HOST_USER,
                        [user.email],
                        fail_silently=False,
                    )
                    
                    messages.success(request, 'Your password has been reset successfully!')
                    return redirect('login')
                except User.DoesNotExist:
                    messages.error(request, 'Invalid user. Please start the reset process again.')
                    return redirect('forgot_password')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordManagementForm(
            user=request.user if request.user.is_authenticated else None,
            stage=stage
        )
    
    return render(request, 'users/password_management.html', {
        'form': form,
        'stage': stage,
        'is_authenticated': request.user.is_authenticated
    })




def forgot_password(request):
    """View to initiate password reset process"""
    request.session['password_stage'] = 'request_code'
    return redirect('password_management')

import secrets

def user_management_view(request):
    # Filter to show only students (not lecturers or other staff)
    users = User.objects.filter(
        is_student=True  # Only show students
    ).order_by('-date_joined')
    
    context = {
        'users': users,
    }
    return render(request, 'secretary_user_list.html', context)