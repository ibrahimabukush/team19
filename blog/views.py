# blog/views.py - Complete file with all functions

from datetime import timedelta
from itertools import count
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from django.contrib import messages
from django.db.models import Count

from dotenv import load_dotenv
from pathlib import Path
import os
import json
import base64
import traceback
import re

from openai import OpenAI

# Import your models
from .models import ChatHistory, ScheduleRequest, AcademicRequest, Post
from users.models import LecturerProfile, Subject
import users.views

User = get_user_model()

# Load OpenAI API
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# ============================================================================
# SCHEDULE REQUEST VIEWS
# ============================================================================

@login_required
def schedule_request(request):
    """Display schedule request form - simplified for secretary handling"""
    try:
        print(f"🔍 Schedule request view called for user: {request.user.username}")
        print(f"🏢 User department: '{request.user.department}'")
        
        context = {
            'user_department': request.user.department,
        }
        
        return render(request, 'blog/schedule_requests.html', context)
        
    except Exception as e:
        print(f"❌ Error in schedule_requests view: {str(e)}")
        messages.error(request, 'שגיאה בטעינת הטופס')
        return render(request, 'blog/schedule_requests.html', {'error_message': str(e)})

@login_required
def submit_schedule_request(request):
    """Submit schedule request"""
    if request.method == 'POST':
        request_type_hebrew = request.POST.get('request_type')
        description = request.POST.get('request_text')
        attachment = request.FILES.get('attachment')
        
        # Map Hebrew text to model values
        request_type_mapping = {
            'שינוי מערכת שעות': 'schedule_change',
            'בקשות הארכת זמן': 'extension_request',
            'בקשה למועד מיוחד': 'special_exam_date',
            'בקשת היעדרות מאושרת': 'approved_absence',
        }
        
        request_type = request_type_mapping.get(request_type_hebrew, request_type_hebrew)
        
        # Validate required fields
        if not description:
            return JsonResponse({'status': 'error', 'message': 'אנא תאר את בקשתך'})
        
        if not request_type_hebrew:
            return JsonResponse({'status': 'error', 'message': 'אנא בחר סוג בקשה'})
        
        try:
            # Create the schedule request
            schedule_request = ScheduleRequest.objects.create(
                student=request.user,
                request_type=request_type,
                request_text=description,
                attachment=attachment,
                status='pending'
            )
            
            messages.success(request, 'הבקשה שלך הוגשה בהצלחה!')
            return JsonResponse({'status': 'success', 'message': 'הבקשה הוגשה בהצלחה'})
            
        except Exception as e:
            print(f"Error creating schedule request: {str(e)}")
            return JsonResponse({'status': 'error', 'message': f'שגיאה: {str(e)}'})
    
    return redirect('schedule_requests')

@login_required
def schedule_request_view(request):
    """View for displaying the schedule request form (legacy support)"""
    return redirect('schedule_requests')

@login_required
def schedule_requests_list(request):
    """View for listing all schedule requests for a student"""
    requests = ScheduleRequest.objects.filter(student=request.user).order_by('-created_at')
    return render(request, 'blog/schedule_requests.html', {'requests': requests})

@login_required
def schedule_request_detail(request, request_id):
    """View for displaying the details of a specific schedule request"""
    try:
        schedule_request = ScheduleRequest.objects.get(id=request_id, student=request.user)
        return render(request, 'blog/schedule_requests.html', {'request': schedule_request})
    except ScheduleRequest.DoesNotExist:
        return redirect('schedule_requests_list')
# ============================================================================
# MAIN PAGE VIEWS
# ============================================================================

def home(request):
    """Home page view"""
    if request.user.is_authenticated:
        if request.user.is_secretary:
            return redirect('secretary_dashboard')
    
    posts = Post.objects.all().order_by('-date_posted')
    return render(request, 'blog/home.html', {'posts': posts})

def about(request):
    """About page view"""
    return render(request, 'blog/about.html', {'title': 'About'})

def services(request):
    """Services page view"""
    return render(request, 'blog/services.html', {'title': 'Services'})

def contact(request):
    """Contact page view"""
    return render(request, 'blog/contact.html', {'title': 'Contact'})

# ============================================================================
# ACADEMIC REQUEST VIEWS
# ============================================================================

@login_required
def academic_request(request):
    """Load academic request form with subjects for user's department"""
    try:
        print(f"🔍 Academic request view called for user: {request.user.username}")
        print(f"🏢 User department: '{request.user.department}'")
        
        # Get subjects for user's exact department
        subjects = Subject.objects.filter(
            department=request.user.department
        ).select_related('lecturer').order_by('name')
        
        print(f"📚 Found {subjects.count()} subjects for department '{request.user.department}'")
        
        # Create subjects data for template
        subjects_data = []
        for subject in subjects:
            # Get lecturer name with fallback
            lecturer_first_name = getattr(subject.lecturer, 'first_name', '') or ''
            lecturer_last_name = getattr(subject.lecturer, 'last_name', '') or ''
            
            if lecturer_first_name.strip() and lecturer_last_name.strip():
                lecturer_name = f"{lecturer_first_name} {lecturer_last_name}".strip()
            else:
                lecturer_name = getattr(subject.lecturer, 'username', 'לא זמין')
            
            subject_data = {
                'name': subject.name,
                'lecturer_full_name': lecturer_name,
                'department': subject.department
            }
            
            subjects_data.append(subject_data)
            print(f"📖 Added subject: {subject.name} - 👨‍🏫 {lecturer_name}")
        
        print(f"📤 Context subjects count: {len(subjects_data)}")
        
        context = {
            'subjects': subjects_data,
            'subjects_count': len(subjects_data),
            'user_department': request.user.department,
        }
        
        return render(request, 'blog/academic_request.html', context)
        
    except Exception as e:
        print(f"❌ Error in academic_request view: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, 'שגיאה בטעינת הקורסים')
        
        context = {
            'subjects': [],
            'subjects_count': 0,
            'error_message': str(e)
        }
        return render(request, 'blog/academic_request.html', context)

@login_required
def get_lecturer(request):
    """API endpoint to get lecturer information for a specific subject"""
    subject_name = request.GET.get('subject')
    
    if not subject_name:
        return JsonResponse({'lecturer_name': None, 'lecturer_id': None})
    
    try:
        print(f"🔍 Looking for subject: {subject_name}")
        print(f"🏢 In department: {request.user.department}")
        
        # Find subject in user's department
        subject = Subject.objects.select_related('lecturer').filter(
            name=subject_name,
            department=request.user.department
        ).first()
        
        if not subject:
            print(f"❌ Subject '{subject_name}' not found in department: {request.user.department}")
            return JsonResponse({
                'lecturer_name': None, 
                'lecturer_id': None,
                'error': 'Subject not found'
            })
        
        # Get lecturer name with fallback
        lecturer_first_name = getattr(subject.lecturer, 'first_name', '') or ''
        lecturer_last_name = getattr(subject.lecturer, 'last_name', '') or ''
        
        if lecturer_first_name.strip() and lecturer_last_name.strip():
            lecturer_name = f"{lecturer_first_name} {lecturer_last_name}".strip()
        else:
            lecturer_name = getattr(subject.lecturer, 'username', 'לא זמין')
        
        print(f"✅ Found lecturer: {lecturer_name}")
        
        return JsonResponse({
            'lecturer_name': lecturer_name,
            'lecturer_id': subject.lecturer.id if subject.lecturer else None
        })
        
    except Exception as e:
        print(f"❌ Error in get_lecturer: {str(e)}")
        return JsonResponse({
            'lecturer_name': None, 
            'lecturer_id': None,
            'error': 'Internal server error'
        })

@login_required
def submit_request(request):
    """Submit academic request"""
    if request.method == 'POST':
        request_type_hebrew = request.POST.get('request_type')
        subject_name = request.POST.get('subject')
        description = request.POST.get('request_text')
        attachment = request.FILES.get('attachment')
        
        # Map Hebrew text to model values
        request_type_mapping = {
            'אישורי רישום או ציונים': 'enrollment_confirmation',
            'ערעורים אקדמיים': 'academic_appeal',
            'בקשות לבדיקת מבחנים': 'exam_review',
        }
        
        request_type = request_type_mapping.get(request_type_hebrew, request_type_hebrew)
        
        # Validate required fields
        if not description:
            return JsonResponse({'status': 'error', 'message': 'אנא תאר את בקשתך'})
        
        # For lecturer-related requests, validate subject selection
        lecturer_request_types = ['academic_appeal', 'exam_review']
        if request_type in lecturer_request_types and not subject_name:
            return JsonResponse({'status': 'error', 'message': 'אנא בחר קורס'})
        
        try:
            # Create the request
            academic_request = AcademicRequest.objects.create(
                student=request.user,
                subject=subject_name if subject_name else '',
                request_type=request_type,
                request_text=description,
                attachment=attachment,
                status='pending'
            )
            
            messages.success(request, 'הבקשה שלך הוגשה בהצלחה!')
            return JsonResponse({'status': 'success', 'message': 'הבקשה הוגשה בהצלחה'})
            
        except Exception as e:
            print(f"Error creating academic request: {str(e)}")
            return JsonResponse({'status': 'error', 'message': f'שגיאה: {str(e)}'})
    
    return redirect('academic_request')

# In blog/views.py, find your update_request_status function

@login_required
def update_request_status(request, request_id):
    """Update request status for any request type (academic, schedule, or personal) with file upload support"""
    if request.method == 'POST':
        try:
            new_status = request.POST.get('status')
            request_type = request.POST.get('request_type', '').lower()
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
            
            # Check that the status is valid
            valid_statuses = ['pending', 'in_progress', 'need_update', 'approved', 'rejected']
            if new_status not in valid_statuses:
                print(f"❌ DEBUGGING: Invalid status: {new_status}")
                return JsonResponse({
                    'success': False,
                    'message': 'סטטוס לא תקין'
                })
            
            # Try to find the request in all three models
            request_obj = None
            model_name = ""
            
            # Order of checking: Academic -> Schedule -> Personal
            print(f"🔍 DEBUGGING: Searching for request ID {request_id} in all models...")
            
            # Check Academic requests
            try:
                request_obj = AcademicRequest.objects.get(id=request_id)
                model_name = "Academic"
                print(f"✅ DEBUGGING: Found Academic request: {request_id}")
            except AcademicRequest.DoesNotExist:
                print(f"❌ DEBUGGING: Academic request {request_id} not found")
            
            # Check Schedule requests if not found in Academic
            if not request_obj:
                try:
                    request_obj = ScheduleRequest.objects.get(id=request_id)
                    model_name = "Schedule"
                    print(f"✅ DEBUGGING: Found Schedule request: {request_id}")
                except ScheduleRequest.DoesNotExist:
                    print(f"❌ DEBUGGING: Schedule request {request_id} not found")
            
            # Check Personal requests if not found in previous models
            if not request_obj:
                try:
                    request_obj = PersonalRequest.objects.get(id=request_id)
                    model_name = "Personal"
                    print(f"✅ DEBUGGING: Found Personal request: {request_id}")
                except PersonalRequest.DoesNotExist:
                    print(f"❌ DEBUGGING: Personal request {request_id} not found")
            
            # If request not found in any model
            if not request_obj:
                print(f"❌ DEBUGGING: Request not found in ANY model with ID: {request_id}")
                return JsonResponse({
                    'success': False,
                    'message': 'בקשה לא נמצאה'
                })
            
            # Determine user role
            user_profile = getattr(request.user, 'profile', None)
            is_lecturer = hasattr(request.user, 'lecturerprofile')
            is_secretary = hasattr(request.user, 'secretaryprofile') or (user_profile and user_profile.role == 'secretary')
            
            # Update the status
            old_status = request_obj.status
            request_obj.status = new_status
            
            # Handle notes based on user role
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
                    # Fallback for models that only have lecturer_note field
                    request_obj.lecturer_note = secretary_note
                    print(f"📝 DEBUGGING: Updated note (via lecturer_note field): {secretary_note[:50]}...")
                else:
                    print(f"⚠️ DEBUGGING: No note field found for {model_name} request")
            
            # Handle file uploads based on user role
            if is_lecturer and lecturer_file:
                if hasattr(request_obj, 'lecturer_file'):
                    # Validate file size (10MB limit)
                    if lecturer_file.size > 10 * 1024 * 1024:
                        return JsonResponse({
                            'success': False,
                            'message': 'גודל הקובץ חורג מ-10MB'
                        })
                    
                    # Validate file type
                    allowed_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.jpg', '.jpeg', '.png']
                    file_extension = os.path.splitext(lecturer_file.name)[1].lower()
                    if file_extension not in allowed_extensions:
                        return JsonResponse({
                            'success': False,
                            'message': 'סוג קובץ לא נתמך'
                        })
                    
                    request_obj.lecturer_file = lecturer_file
                    request_obj.lecturer_file_name = lecturer_file.name
                    request_obj.lecturer_file_uploaded_at = timezone.now()
                    print(f"📎 DEBUGGING: Uploaded lecturer file: {lecturer_file.name}")
                else:
                    print(f"⚠️ DEBUGGING: No lecturer_file field in {model_name} model")
            
            if is_secretary and secretary_file:
                if hasattr(request_obj, 'secretary_file'):
                    # Validate file size (10MB limit)
                    if secretary_file.size > 10 * 1024 * 1024:
                        return JsonResponse({
                            'success': False,
                            'message': 'גודל הקובץ חורג מ-10MB'
                        })
                    
                    # Validate file type
                    allowed_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.jpg', '.jpeg', '.png']
                    file_extension = os.path.splitext(secretary_file.name)[1].lower()
                    if file_extension not in allowed_extensions:
                        return JsonResponse({
                            'success': False,
                            'message': 'סוג קובץ לא נתמך'
                        })
                    
                    request_obj.secretary_file = secretary_file
                    request_obj.secretary_file_name = secretary_file.name
                    request_obj.secretary_file_uploaded_at = timezone.now()
                    print(f"📎 DEBUGGING: Uploaded secretary file: {secretary_file.name}")
                else:
                    print(f"⚠️ DEBUGGING: No secretary_file field in {model_name} model")
            
            # Handle update deadline for requests that need updates
            if new_status == 'need_update' and update_deadline:
                if hasattr(request_obj, 'update_deadline'):
                    from datetime import datetime
                    try:
                        # Parse the date string
                        deadline_date = datetime.strptime(update_deadline, '%Y-%m-%d').date()
                        request_obj.update_deadline = deadline_date
                        print(f"📅 DEBUGGING: Set update deadline to: {deadline_date}")
                    except ValueError as e:
                        print(f"❌ DEBUGGING: Invalid date format: {update_deadline}, error: {e}")
            elif new_status != 'need_update' and hasattr(request_obj, 'update_deadline'):
                # Clear deadline if status is not 'need_update'
                request_obj.update_deadline = None
            
            # Save the request
            request_obj.save()
            
            print(f"✅ DEBUGGING: {model_name} request {request_id} status updated: {old_status} -> {new_status}")

            # --- Re-fetch immediately after save to verify ---
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
            return JsonResponse({
                'success': False,
                'message': f'שגיאה: {str(e)}'
            })
    
    print(f"⚠️ DEBUGGING: Invalid request method: {request.method}")
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
import os
@login_required
def update_request_status(request, request_id):
    """Update request status and fields for any request type with file upload support"""
    if request.method == 'POST':
        try:
            new_status = request.POST.get('status')
            request_type_hint = request.POST.get('request_type', '').lower()
            secretary_note = request.POST.get('secretary_note', '')
            lecturer_note = request.POST.get('lecturer_note', '')
            update_deadline = request.POST.get('update_deadline')
            
            # For PersonalRequest extra fields
            new_request_text = request.POST.get('request_text')
            new_request_type = request.POST.get('request_type_value')  # Or 'request_type' if you use that name
            
            lecturer_file = request.FILES.get('lecturer_file')
            secretary_file = request.FILES.get('secretary_file')
            
            valid_statuses = ['pending', 'in_progress', 'need_update', 'approved', 'rejected']
            if new_status not in valid_statuses:
                return JsonResponse({'success': False, 'message': 'סטטוס לא תקין'})
            
            request_obj = None
            model_name = ""
            
            # Try find request by ID in order
            try:
                request_obj = AcademicRequest.objects.get(id=request_id)
                model_name = "Academic"
            except AcademicRequest.DoesNotExist:
                try:
                    request_obj = ScheduleRequest.objects.get(id=request_id)
                    model_name = "Schedule"
                except ScheduleRequest.DoesNotExist:
                    try:
                        request_obj = PersonalRequest.objects.get(id=request_id)
                        model_name = "Personal"
                    except PersonalRequest.DoesNotExist:
                        return JsonResponse({'success': False, 'message': 'בקשה לא נמצאה'})
            
            # Determine user roles
            user_profile = getattr(request.user, 'profile', None)
            is_lecturer = hasattr(request.user, 'lecturerprofile')
            is_secretary = hasattr(request.user, 'secretaryprofile') or (user_profile and user_profile.role == 'secretary')
            
            old_status = request_obj.status
            request_obj.status = new_status
            
            # Notes update
            if is_lecturer and lecturer_note and hasattr(request_obj, 'lecturer_note'):
                request_obj.lecturer_note = lecturer_note
            
            if is_secretary:
                if secretary_note:
                    if hasattr(request_obj, 'secretary_note'):
                        request_obj.secretary_note = secretary_note
                    elif hasattr(request_obj, 'lecturer_note'):
                        request_obj.lecturer_note = secretary_note
            
            # PersonalRequest specific fields update
            if model_name == "Personal":
                if new_request_text is not None:
                    request_obj.request_text = new_request_text
                
                if new_request_type is not None:
                    request_obj.request_type = new_request_type
            
            # File uploads validation and save
            allowed_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.jpg', '.jpeg', '.png']
            max_size = 10 * 1024 * 1024  # 10MB
            
            if is_lecturer and lecturer_file and hasattr(request_obj, 'lecturer_file'):
                if lecturer_file.size > max_size:
                    return JsonResponse({'success': False, 'message': 'גודל הקובץ חורג מ-10MB'})
                ext = os.path.splitext(lecturer_file.name)[1].lower()
                if ext not in allowed_extensions:
                    return JsonResponse({'success': False, 'message': 'סוג קובץ לא נתמך'})
                request_obj.lecturer_file = lecturer_file
                request_obj.lecturer_file_name = lecturer_file.name
                request_obj.lecturer_file_uploaded_at = timezone.now()
            
            if is_secretary and secretary_file and hasattr(request_obj, 'secretary_file'):
                if secretary_file.size > max_size:
                    return JsonResponse({'success': False, 'message': 'גודל הקובץ חורג מ-10MB'})
                ext = os.path.splitext(secretary_file.name)[1].lower()
                if ext not in allowed_extensions:
                    return JsonResponse({'success': False, 'message': 'סוג קובץ לא נתמך'})
                request_obj.secretary_file = secretary_file
                request_obj.secretary_file_name = secretary_file.name
                request_obj.secretary_file_uploaded_at = timezone.now()
            
            # Update deadline for 'need_update' status
            if new_status == 'need_update' and update_deadline and hasattr(request_obj, 'update_deadline'):
                from datetime import datetime
                try:
                    deadline_date = datetime.strptime(update_deadline, '%Y-%m-%d').date()
                    request_obj.update_deadline = deadline_date
                except ValueError:
                    pass
            elif new_status != 'need_update' and hasattr(request_obj, 'update_deadline'):
                request_obj.update_deadline = None
            
            request_obj.save()
            
            return JsonResponse({
                'success': True,
                'message': f'סטטוס עודכן בהצלחה ({model_name})',
                'request_type': model_name.lower(),
                'old_status': old_status,
                'new_status': new_status,
                'file_uploaded': bool(lecturer_file or secretary_file),
                'lecturer_file_uploaded': bool(lecturer_file),
                'secretary_file_uploaded': bool(secretary_file),
            })
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'message': f'שגיאה: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})



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
def get_request_details(request, request_id):
    """Get detailed request information for the modal - filtered by user role"""
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

# Add this URL to your urls.py:
# path('debug_requests/', views.debug_requests, name='debug_requests'),
# ============================================================================
# PERSONAL REQUEST VIEWS
# ============================================================================
from .models import PersonalRequest, User, Subject
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

@login_required
def personal_requests(request):
    """Load personal request form"""
    try:
        print(f"🔍 Personal request view called for user: {request.user.username}")
        print(f"🏢 User department: '{request.user.department}'")
        
        context = {
            'user_department': request.user.department,
        }
        
        return render(request, 'blog/personal_requests.html', context)
        
    except Exception as e:
        print(f"❌ Error in personal_request view: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, 'שגיאה בטעינת הטופס')
        
        context = {
            'error_message': str(e)
        }
        return render(request, 'blog/personal_requests.html', context)

@login_required
def get_department_lecturers(request):
    """Get lecturers from the user's department"""
    try:
        print(f"🔍 Loading lecturers for department: {request.user.department}")
        
        # Get lecturers from the user's department
        lecturers = User.objects.filter(
            is_lecturer=True,
            department=request.user.department
        ).prefetch_related('taught_subjects')
        
        lecturer_data = []
        for lecturer in lecturers:
            # Get subjects taught by this lecturer
            subjects = lecturer.taught_subjects.all()
            subject_names = [subject.name for subject in subjects]
            
            lecturer_info = {
                'id': lecturer.id,
                'username': lecturer.username,
                'full_name': lecturer.get_full_name(),
                'email': lecturer.email,
                'subjects': subject_names
            }
            lecturer_data.append(lecturer_info)
        
        print(f"✅ Found {len(lecturer_data)} lecturers in department {request.user.department}")
        
        return JsonResponse({
            'status': 'success',
            'lecturers': lecturer_data
        })
        
    except Exception as e:
        print(f"❌ Error loading lecturers: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'status': 'error',
            'message': f'שגיאה בטעינת רשימת המרצים: {str(e)}'
        })

@login_required
def submit_personal_requests(request):
    """Submit personal request"""
    if request.method == 'POST':
        request_type_hebrew = request.POST.get('request_type')
        description = request.POST.get('request_text')
        selected_lecturer_id = request.POST.get('selected_lecturer')
        attachment = request.FILES.get('attachment')
        
        # Map Hebrew text to model values
        request_type_mapping = {
            'בקשה למכתבי המלצה': 'recommendation_letter',
            'בקשות מלגות וסיוע כלכלי': 'scholarships_financial_aid',
            'בקשת שינוי סטטוס אקדמי': 'academic_status_change',
            'פניה כללית למנהל': 'general_manager_inquiry',
        }
        
        request_type = request_type_mapping.get(request_type_hebrew, request_type_hebrew)
        
        # Validate required fields
        if not description:
            return JsonResponse({'status': 'error', 'message': 'אנא תאר את בקשתך'})
        
        if not request_type_hebrew:
            return JsonResponse({'status': 'error', 'message': 'אנא בחר סוג בקשה'})
        
        # For recommendation letter requests, validate lecturer selection
        if request_type == 'recommendation_letter':
            if not selected_lecturer_id:
                return JsonResponse({'status': 'error', 'message': 'אנא בחר מרצה למכתב ההמלצה'})
            
            # Validate that the selected lecturer exists and is from the same department
            try:
                selected_lecturer = User.objects.get(
                    id=selected_lecturer_id,
                    is_lecturer=True,
                    department=request.user.department
                )
            except User.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'המרצה שנבחר לא תקין'})
        
        try:
            print(f"📝 Creating personal request for user: {request.user.username}")
            print(f"📋 Request type: {request_type_hebrew} -> {request_type}")
            print(f"📄 Description length: {len(description)} characters")
            
            if request_type == 'recommendation_letter':
                print(f"👨‍🏫 Selected lecturer: {selected_lecturer.get_full_name()} (ID: {selected_lecturer.id})")
            
            # Create the request
            personal_request = PersonalRequest.objects.create(
                student=request.user,
                request_type=request_type,
                request_text=description,
                attachment=attachment,
                status='pending'
            )
            
            # If it's a recommendation letter request, store the lecturer information
            if request_type == 'recommendation_letter' and selected_lecturer_id:
                # You might want to add a field to store lecturer info or handle it differently
                # For now, we'll add it to the request text
                lecturer_info = f"\n\nמרצה נבחר: {selected_lecturer.get_full_name()} ({selected_lecturer.email})"
                personal_request.request_text += lecturer_info
                personal_request.save()
            
            print(f"✅ Personal request created successfully with ID: {personal_request.id}")
            
            messages.success(request, 'הבקשה שלך הוגשה בהצלחה!')
            return JsonResponse({'status': 'success', 'message': 'הבקשה הוגשה בהצלחה'})
            
        except Exception as e:
            print(f"❌ Error creating personal request: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'status': 'error', 'message': f'שגיאה: {str(e)}'})
    
    print(f"⚠️ Invalid request method: {request.method}")
    return redirect('personal_request')

@login_required
def personal_request_detail(request, request_id):
    """View personal request details"""
    try:
        print(f"📖 Loading personal request detail for ID: {request_id}")
        
        personal_request = get_object_or_404(PersonalRequest, id=request_id)
        
        # Check if user can view this request
        if personal_request.student != request.user and not request.user.is_staff:
            print(f"🚫 Access denied for user {request.user.username} to request {request_id}")
            messages.error(request, 'אין לך הרשאה לצפות בבקשה זו')
            return redirect('personal_request')
        
        print(f"✅ Personal request loaded successfully: {personal_request.request_type}")
        
        context = {
            'request': personal_request,
            'can_edit': request.user.is_staff
        }
        
        return render(request, 'blog/personal_request_detail.html', context)
        
    except PersonalRequest.DoesNotExist:
        print(f"❌ Personal request not found with ID: {request_id}")
        messages.error(request, 'בקשה לא נמצאה')
        return redirect('personal_request')
    except Exception as e:
        print(f"❌ Error loading personal request detail: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, 'שגיאה בטעינת פרטי הבקשה')
        return redirect('personal_request')

@login_required
def personal_request_list(request):
    """List all personal requests for current user or all requests for staff"""
    try:
        print(f"📋 Loading personal request list for user: {request.user.username}")
        
        if request.user.is_staff:
            # Staff can see all requests
            requests = PersonalRequest.objects.all().select_related('student').order_by('-created_at')
            print(f"👩‍💼 Staff user - showing all {requests.count()} personal requests")
        else:
            # Students see only their own requests
            requests = PersonalRequest.objects.filter(student=request.user).order_by('-created_at')
            print(f"👨‍🎓 Student user - showing {requests.count()} personal requests")
        
        # Get status counts for dashboard
        status_counts = {
            'pending': requests.filter(status='pending').count(),
            'in_progress': requests.filter(status='in_progress').count(),
            'approved': requests.filter(status='approved').count(),
            'rejected': requests.filter(status='rejected').count(),
        }
        
        print(f"📊 Status counts: {status_counts}")
        
        context = {
            'requests': requests,
            'status_counts': status_counts,
            'is_staff': request.user.is_staff
        }
        
        return render(request, 'blog/personal_request_list.html', context)
        
    except Exception as e:
        print(f"❌ Error loading personal request list: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, 'שגיאה בטעינת רשימת הבקשות')
        
        context = {
            'requests': [],
            'status_counts': {},
            'error_message': str(e)
        }
        return render(request, 'blog/personal_request_list.html', context)
# ============================================================================
# SCHEDULE REQUEST VIEWS
# ============================================================================

@login_required
def schedule_request(request):
    """Display schedule request form"""
    return render(request, 'blog/schedule_requests.html')

@login_required
def schedule_request_view(request):
    """View for displaying the schedule request form"""
    return render(request, 'blog/schedule_requests.html')

@login_required
def submit_schedule_request(request):
    """API endpoint for submitting a new schedule request"""
    if request.method == "POST":
        request_type = request.POST.get('request_type')
        request_text = request.POST.get('request_text')
        
        # Create the new request
        new_request = ScheduleRequest(
            student=request.user,
            request_type=request_type,
            request_text=request_text
        )
        new_request.save()
        
        return JsonResponse({"status": "success", "message": "הבקשה נשלחה בהצלחה!"})
    
    return JsonResponse({"status": "error", "message": "שגיאה בשליחת הבקשה"}, status=400)

@login_required
def schedule_requests_list(request):
    """View for listing all schedule requests for a student"""
    requests = ScheduleRequest.objects.filter(student=request.user).order_by('-created_at')
    return render(request, 'blog/schedule_requests.html', {'requests': requests})

@login_required
def schedule_request_detail(request, request_id):
    """View for displaying the details of a specific schedule request"""
    try:
        schedule_request = ScheduleRequest.objects.get(id=request_id, student=request.user)
        return render(request, 'blog/schedule_requests.html', {'request': schedule_request})
    except ScheduleRequest.DoesNotExist:
        return redirect('schedule_requests_list')

# ============================================================================
# TRACKING AND MONITORING VIEWS
# ============================================================================

from itertools import chain
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

# In blog/views.py, find your tracking function

@login_required
def tracking(request):
    """Track user's academic, schedule, and personal requests."""

    # --- MODIFIED LOGIC HERE: Removed the .exclude() filter ---
    academic_requests = AcademicRequest.objects.filter(student=request.user)
    schedule_requests = ScheduleRequest.objects.filter(student=request.user)
    personal_requests = PersonalRequest.objects.filter(student=request.user)
    # --- END MODIFIED LOGIC ---

    user_requests = list(chain(academic_requests, schedule_requests, personal_requests))

    # Optional: Add back the debugging prints if you still need them
    # print(f"\n--- DEBUGGING TRACKING VIEW for user: {request.user.username} ---")
    # if not user_requests:
    #     print("No active requests found for this user.")
    # else:
    #     for req in user_requests:
    #         model_type = req.__class__.__name__
    #         print(f"  Request ID: {req.id}, Type: {model_type}, Status: {req.status}, Created: {req.created_at}")
    #         if hasattr(req, 'update_deadline') and req.update_deadline:
    #             print(f"    Update Deadline: {req.update_deadline}")
    #         if hasattr(req, 'secretary_note') and req.secretary_note:
    #             print(f"    Secretary Note: {req.secretary_note[:50]}...")
    #         elif hasattr(req, 'lecturer_note') and req.lecturer_note:
    #             print(f"    Lecturer Note: {req.lecturer_note[:50]}...")
    # print("--- END DEBUGGING TRACKING VIEW ---\n")


    # Sort all requests by creation date, newest first
    user_requests.sort(key=lambda x: x.created_at, reverse=True)

    for req in user_requests:
        req.is_past_deadline = (
            hasattr(req, 'status') and req.status == "need_update"
            and hasattr(req, 'update_deadline') and req.update_deadline
            and timezone.now() > req.update_deadline
        )

    return render(request, 'blog/tracking.html', {'requests': user_requests})


from django.utils.dateformat import format
from itertools import chain

def serialize_request(req):
    return {
        "id": req.id,
        "status": req.status,
        "subject": getattr(req, "subject", None),
        "request_type": getattr(req, "request_type", None),
        "created_at": format(req.created_at, "Y-m-d H:i") if req.created_at else None,
        "review_started_at": format(getattr(req, "review_started_at", None), "Y-m-d H:i") if getattr(req, "review_started_at", None) else None,
        "update_requested_at": format(getattr(req, "update_requested_at", None), "Y-m-d H:i") if getattr(req, "update_requested_at", None) else None,
        "update_deadline": format(getattr(req, "update_deadline", None), "Y-m-d H:i") if getattr(req, "update_deadline", None) else None,
        "decision_date": format(getattr(req, "decision_date", None), "Y-m-d H:i") if getattr(req, "decision_date", None) else None,
        "completed_at": format(getattr(req, "completed_at", None), "Y-m-d H:i") if getattr(req, "completed_at", None) else None,
    }

@login_required
def chat_history(request):
    """Display chat history for user"""
    history = ChatHistory.objects.filter(username=request.user.username).order_by('-timestamp')
    return render(request, 'blog/chat_history.html', {'history': history})

# ============================================================================
# SECRETARY DASHBOARD
# ============================================================================

@login_required
def secretary_delete_request(request, request_id):
    """Secretary view to delete completed requests"""
    # Check if user is a secretary
    if not request.user.is_secretary:
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    if request.method == 'POST':
        try:
            # Get the request and verify it belongs to secretary's department
            academic_request = AcademicRequest.objects.get(
                id=request_id,
                student__department=request.user.department
            )
            
            # Only allow deletion of completed requests
            if academic_request.status in ['approved', 'rejected']:
                academic_request.delete()
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Can only delete completed requests'})
                
        except AcademicRequest.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Request not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid method'})

@login_required
def secretary_get_request_details(request, request_id):
    """Get request details for secretary modal"""
    # Check if user is a secretary
    if not request.user.is_secretary:
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    try:
        # Get the request and verify it belongs to secretary's department
        academic_request = AcademicRequest.objects.get(
            id=request_id,
            student__department=request.user.department
        )
        
        data = {
            'id': academic_request.id,
            'student_name': academic_request.student.get_full_name() or academic_request.student.username,
            'subject': academic_request.subject,
            'request_type': academic_request.get_request_type_display(),
            'request_text': academic_request.request_text,
            'status': academic_request.status,
            'created_at': academic_request.created_at.strftime('%d/%m/%Y'),
            'lecturer_note': academic_request.lecturer_note or '',
            'update_deadline': academic_request.update_deadline.strftime('%d/%m/%Y') if academic_request.update_deadline else None,
            'update_deadline_raw': academic_request.update_deadline.strftime('%Y-%m-%d') if academic_request.update_deadline else '',
            'is_past_deadline': academic_request.is_past_deadline() if hasattr(academic_request, 'is_past_deadline') else False,
        }
        
        return JsonResponse(data)
        
    except AcademicRequest.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Request not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
def delete_request(request, request_id):
    if request.method == 'POST':
        try:
            academic_request = AcademicRequest.objects.get(id=request_id)
            academic_request.delete()
            return JsonResponse({'success': True})
        except AcademicRequest.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Request not found'})
    return JsonResponse({'success': False, 'error': 'Invalid method'})
from django.db.models import Q
from .models import AcademicRequest, ScheduleRequest

@login_required
def secretary_dashboard(request):
    """Secretary dashboard for managing secretary-specific requests only"""
    # Check if user is a secretary
    if not request.user.is_secretary:
        messages.error(request, 'הגישה מותרת למזכירות בלבד.')
        return redirect('blog-home')
    
    # Define which request types are handled by secretaries vs lecturers
    secretary_academic_types = [
        'enrollment_confirmation',  # אישורי רישום או ציונים
        # Add other secretary-specific academic types here if any
    ]
    
    lecturer_academic_types = [
        'academic_appeal',  # ערעורים אקדמיים
        'exam_review',      # בקשות לבדיקת מבחנים
    ]
    
    # Get academic requests ONLY for secretary-handled types from students in the same department
    academic_requests = AcademicRequest.objects.filter(
        student__department=request.user.department,
        request_type__in=secretary_academic_types
    ).order_by('-created_at')
    
    # Get schedule requests (all schedule requests are handled by secretaries)
    schedule_requests = ScheduleRequest.objects.filter(
        student__department=request.user.department
    ).order_by('-created_at')
    
    # Get personal requests (secretaries handle specific types)
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
    
    personal_requests = PersonalRequest.objects.filter(
        student__department=request.user.department,
        request_type__in=secretary_personal_types
    ).order_by('-created_at')
    
    # Debug logging
    print(f"Secretary: {request.user.username}, Department: {request.user.department}")
    print(f"Academic requests found (secretary types only): {academic_requests.count()}")
    print(f"Schedule requests found: {schedule_requests.count()}")
    print(f"Personal requests found (secretary types only): {personal_requests.count()}")
    
    # Combine all types of requests for display
    all_requests = list(academic_requests) + list(schedule_requests) + list(personal_requests)
    # Sort combined list by created_at
    all_requests.sort(key=lambda x: x.created_at, reverse=True)
    
    # Filter by status if provided
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        filtered_requests = [req for req in all_requests if req.status == status_filter]
    else:
        filtered_requests = all_requests
    
    # Get combined statistics
    total_academic = academic_requests.count()
    total_schedule = schedule_requests.count()
    total_personal = personal_requests.count()
    
    stats = {
        'total': total_academic + total_schedule + total_personal,
        'pending': len([req for req in all_requests if req.status == 'pending']),
        'in_progress': len([req for req in all_requests if req.status == 'in_progress']),
        'need_update': len([req for req in all_requests if req.status == 'need_update']),
        'approved': len([req for req in all_requests if req.status == 'approved']),
        'rejected': len([req for req in all_requests if req.status == 'rejected']),
        'academic_total': total_academic,
        'schedule_total': total_schedule,
        'personal_total': total_personal,
    }
    
    # Get requests by type (combined from secretary-handled models only)
    academic_types = academic_requests.values('request_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    schedule_types = schedule_requests.values('request_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    personal_types = personal_requests.values('request_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Combine request types statistics
    request_types_stats = list(academic_types) + list(schedule_types) + list(personal_types)
    
    # Format request types for display
    type_display_names = {
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
    
    for stat in request_types_stats:
        stat['display_name'] = type_display_names.get(stat['request_type'], stat['request_type'])
    
    # Get urgent requests (pending for more than 3 days) from secretary-handled requests only
    three_days_ago = timezone.now() - timedelta(days=3)
    urgent_academic = academic_requests.filter(
        status='pending',
        created_at__lte=three_days_ago
    )
    urgent_schedule = schedule_requests.filter(
        status='pending',
        created_at__lte=three_days_ago
    )
    urgent_personal = personal_requests.filter(
        status='pending',
        created_at__lte=three_days_ago
    )
    urgent_requests = list(urgent_academic) + list(urgent_schedule) + list(urgent_personal)
    urgent_requests.sort(key=lambda x: x.created_at, reverse=True)
    
    # Department names mapping
    department_names = {
        'מדעי המחשב': 'מדעי המחשב',
        'הנדסת תוכנה': 'הנדסת תוכנה',
        'הנדסת אלקטרוניקה': 'הנדסת אלקטרוניקה',
    }
    
    department_display = department_names.get(request.user.department, request.user.department)
    
    context = {
        'all_requests': all_requests,
        'filtered_requests': filtered_requests,
        'urgent_requests': urgent_requests,
        'stats': stats,
        'request_types_stats': request_types_stats,
        'status_filter': status_filter,
        'department_display': department_display,
        'three_days_ago': three_days_ago,
        'academic_requests': academic_requests,
        'schedule_requests': schedule_requests,
        'personal_requests': personal_requests,
        # Add info about which types are handled by secretary vs lecturer
        'secretary_handled_types': {
            'academic': secretary_academic_types,
            'personal': secretary_personal_types,
        },
        'lecturer_handled_types': {
            'academic': lecturer_academic_types,
            'personal': lecturer_personal_types,
        }
    }
    
    return render(request, 'blog/secretary_dashboard.html', context)
# ============================================================================
# CHATBOT VIEWS
# ============================================================================

@csrf_exempt
def chatbot_response(request):
    """Handle chatbot interactions"""
    print(f"Request method: {request.method}")
    print(f"POST data: {request.POST}")
    
    if request.method == "POST":
        try:
            user_message = request.POST.get("message", "")
            print(f"User message: {user_message}")
            
            username = "Anonymous"
            if request.user.is_authenticated:
                username = request.user.username

            system_prompt = """
You are ISEND Assistant, a smart, friendly virtual helper for university students.

🎓 You ONLY help with these 6 official student request types:
1. Academic Appeal
2. Enrollment Certificate
3. Exam Review
4. Schedule Change
5. Personal Information Update
6. Recommendation Letter

💬 Use simple, friendly language. Be polite and helpful.

💡 Recognize common phrases students might use — not just the official names.
Your goal is to understand what the student means and guide them step-by-step.

---

1. **Academic Appeal**
- ✅ Keywords: unfair grade, wrong grade, low grade, grade issue, appeal grade, grade complaint, teacher not fair, submit appeal, exam not graded right, fight my grade
- 📍 Instructions:
  - Go to Services → Academic Requests → Appeals
  - Fill: Full Name, Student ID, Course Name, Reason
  - 📎 Upload: A PDF/letter explaining the issue. Optionally add grade reports or lecturer emails.
  - Track request under 'My Requests'

---

2. **Enrollment Certificate**
- ✅ Keywords: proof I'm a student, enrollment document, certificate, official paper, confirmation letter, proof of studies, student status, for scholarship, get official doc
- 📍 Instructions:
  - Go to Services → Academic Requests → Official Document
  - Choose "Enrollment Confirmation"
  - Fill in name and student ID
  - 📎 No upload needed – the system will generate the certificate

---

3. **Exam Review**
- ✅ Keywords: exam correction, recheck exam, unfair exam, exam review, wrong exam result, review test, exam issue, submit exam request
- 📍 Instructions:
  - Go to Academic Requests → Exam Review
  - Choose the course and exam
  - Write the reason clearly
  - 📎 Upload: Optional – Screenshot of exam or PDF explanation

---

4. **Schedule Change**
- ✅ Keywords: class conflict, overlapping classes, 2 classes same time, time clash, schedule problem, change class, fix schedule, time issue
- 📍 Instructions:
  - Go to Schedule Services
  - Select the course to change
  - Explain the issue clearly
  - 📎 Upload: Screenshot or written explanation (PDF or image)

---

5. **Personal Information Update**
- ✅ Keywords: update number, new address, fix email, change contact info, update profile, wrong details, student info edit
- 📍 Instructions:
  - Go to Profile Settings
  - Edit phone number, email, address
  - 📎 Upload: Only if required by university (ID, utility bill)

---

6. **Recommendation Letter**
- ✅ Keywords: request recommendation, apply for letter, need letter from professor, lecturer reference, academic reference, scholarship letter, get recommendation
- 📍 Instructions:
  - Go to Services → Personal Requests → Recommendation Letter
  - Choose lecturer and reason
  - 📎 Upload: Optional – CV, transcript, or short explanation letter

---

🚫 If the question is unrelated to these 6 requests, politely say:

"I'm sorry, I can only help with official ISEND student requests such as appeals, documents, or schedule changes."

"""

            chat_completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
            )

            reply = chat_completion.choices[0].message.content
            
            # Save chat history
            ChatHistory.objects.create(
                username=username,
                message=user_message,
                reply=reply
            )
            
            return JsonResponse({"reply": reply})

        except Exception as e:
            print("Chatbot error:")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            traceback.print_exc()
            return JsonResponse({"reply": f"Oops! Something went wrong on our end. Error: {type(e).__name__}"})

    return JsonResponse({"reply": "Invalid request method."})

# ============================================================================
# TECHNICAL MANAGEMENT VIEWS
# ============================================================================

def technicalmanagement(request):
    """Display the technical management error reporting form"""
    return render(request, 'blog/technicalmanagement.html')

# views.py - Error Report Views

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.utils import timezone
from .models import ErrorReport, ErrorReportComment, get_error_report_stats
import json

def error_report_form(request):
    """Display the error report form"""
    try:
        print(f"🔍 Error report form accessed by: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
        
        context = {}
        
        # Pre-populate user data if logged in
        if request.user.is_authenticated:
            context['user_name'] = request.user.get_full_name() or request.user.username
            context['user_email'] = request.user.email
        
        return render(request, 'blog/error_report.html', context)
        
    except Exception as e:
        print(f"❌ Error in error_report_form view: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, 'שגיאה בטעינת טופס הדיווח')
        return render(request, 'blog/error_report.html', {'error_message': str(e)})

def submit_error_report(request):
    """Handle error report submission"""
    if request.method == 'POST':
        try:
            print(f"📝 Processing error report submission")
            
            # Extract form data
            reporter_name = request.POST.get('reporter_name', '').strip()
            reporter_email = request.POST.get('reporter_email', '').strip()
            error_type = request.POST.get('error_type', '')
            priority = request.POST.get('priority', 'medium')
            description = request.POST.get('description', '').strip()
            attachment = request.FILES.get('attachment')
            
            # Validate required fields
            if not reporter_name:
                return JsonResponse({'status': 'error', 'message': 'שם המדווח נדרש'})
            
            if not reporter_email:
                return JsonResponse({'status': 'error', 'message': 'אימייל המדווח נדרש'})
            
            if not error_type:
                return JsonResponse({'status': 'error', 'message': 'סוג השגיאה נדרש'})
            
            if not description:
                return JsonResponse({'status': 'error', 'message': 'תיאור השגיאה נדרש'})
            
            # Get technical information
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            ip_address = get_client_ip(request)
            page_url = request.META.get('HTTP_REFERER', '')
            
            # Create error report
            error_report_data = {
                'reporter_name': reporter_name,
                'reporter_email': reporter_email,
                'error_type': error_type,
                'priority': priority,
                'description': description,
                'user_agent': user_agent,
                'ip_address': ip_address,
                'page_url': page_url,
                'attachment': attachment,
                'status': 'new'
            }
            
            # Link to user if authenticated
            if request.user.is_authenticated:
                error_report_data['reporter_user'] = request.user
            
            error_report = ErrorReport.objects.create(**error_report_data)
            
            print(f"✅ Error report created successfully with ID: {error_report.id}")
            print(f"📋 Type: {error_type}, Priority: {priority}")
            print(f"👤 Reporter: {reporter_name} ({reporter_email})")
            
            # Send notification emails
            try:
                send_error_report_notifications(error_report)
            except Exception as email_error:
                print(f"⚠️ Failed to send notification emails: {str(email_error)}")
            
            # Return success response
            return JsonResponse({
                'status': 'success',
                'message': 'דיווח השגיאה נשלח בהצלחה',
                'report_id': error_report.id
            })
            
        except Exception as e:
            print(f"❌ Error creating error report: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'status': 'error',
                'message': f'שגיאה בשמירת הדיווח: {str(e)}'
            })
    
    print(f"⚠️ Invalid request method: {request.method}")
    return JsonResponse({'status': 'error', 'message': 'שיטת בקשה לא תקינה'})
# Add these imports to the top of your blog/views.py file
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.utils import timezone
import json
from django.contrib.auth.decorators import user_passes_test
# Add these views to your existing blog/views.py file

def error_report_form(request):
    """Display the error report form"""
    try:
        print(f"🔍 Error report form accessed by: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
        
        context = {}
        
        # Pre-populate user data if logged in
        if request.user.is_authenticated:
            context['user_name'] = request.user.get_full_name() or request.user.username
            context['user_email'] = request.user.email
        
        return render(request, 'blog/error_report.html', context)
        
    except Exception as e:
        print(f"❌ Error in error_report_form view: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, 'שגיאה בטעינת טופס הדיווח')
        return render(request, 'blog/error_report.html', {'error_message': str(e)})

def submit_error_report(request):
    """Handle error report submission"""
    if request.method == 'POST':
        try:
            print(f"📝 Processing error report submission")
            
            # Extract form data
            reporter_name = request.POST.get('reporter_name', '').strip()
            reporter_email = request.POST.get('reporter_email', '').strip()
            error_type = request.POST.get('error_type', '')
            priority = request.POST.get('priority', 'medium')
            description = request.POST.get('description', '').strip()
            attachment = request.FILES.get('attachment')
            
            # Validate required fields
            if not reporter_name:
                return JsonResponse({'status': 'error', 'message': 'שם המדווח נדרש'})
            
            if not reporter_email:
                return JsonResponse({'status': 'error', 'message': 'אימייל המדווח נדרש'})
            
            if not error_type:
                return JsonResponse({'status': 'error', 'message': 'סוג השגיאה נדרש'})
            
            if not description:
                return JsonResponse({'status': 'error', 'message': 'תיאור השגיאה נדרש'})
            
            # Get technical information
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            ip_address = get_client_ip(request)
            page_url = request.META.get('HTTP_REFERER', '')
            
            # Create error report
            error_report_data = {
                'reporter_name': reporter_name,
                'reporter_email': reporter_email,
                'error_type': error_type,
                'priority': priority,
                'description': description,
                'user_agent': user_agent,
                'ip_address': ip_address,
                'page_url': page_url,
                'attachment': attachment,
                'status': 'new'
            }
            
            # Link to user if authenticated
            if request.user.is_authenticated:
                error_report_data['reporter_user'] = request.user
            
            error_report = ErrorReport.objects.create(**error_report_data)
            
            print(f"✅ Error report created successfully with ID: {error_report.id}")
            print(f"📋 Type: {error_type}, Priority: {priority}")
            print(f"👤 Reporter: {reporter_name} ({reporter_email})")
            
            # Return success response
            return JsonResponse({
                'status': 'success',
                'message': 'דיווח השגיאה נשלח בהצלחה',
                'report_id': error_report.id
            })
            
        except Exception as e:
            print(f"❌ Error creating error report: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'status': 'error',
                'message': f'שגיאה בשמירת הדיווח: {str(e)}'
            })
    
    print(f"⚠️ Invalid request method: {request.method}")
    return JsonResponse({'status': 'error', 'message': 'שיטת בקשה לא תקינה'})

def get_client_ip(request):
    """Get the client's IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@user_passes_test(lambda u: u.is_staff)
def error_report_list(request):
    """List all error reports for staff members"""
    try:
        print(f"📋 Loading error report list for staff user: {request.user.username}")
        
        # Get all error reports
        error_reports = ErrorReport.objects.all().select_related('reporter_user', 'assigned_to').order_by('-created_at')
        
        # Get statistics
        stats = get_error_report_stats()
        
        # Pagination
        paginator = Paginator(error_reports, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        print(f"📊 Found {error_reports.count()} error reports")
        
        context = {
            'error_reports': page_obj,
            'stats': stats,
            'error_type_choices': ErrorReport.ERROR_TYPE_CHOICES,
            'priority_choices': ErrorReport.PRIORITY_CHOICES,
            'status_choices': ErrorReport.STATUS_CHOICES,
        }
        
        return render(request, 'blog/error_report_list.html', context)
        
    except Exception as e:
        print(f"❌ Error loading error report list: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, 'שגיאה בטעינת רשימת הדיווחים')
        return render(request, 'blog/error_report_list.html', {'error_message': str(e)})

@login_required
def my_error_reports(request):
    """List error reports submitted by the current user"""
    try:
        print(f"📋 Loading error reports for user: {request.user.username}")
        
        # Get reports by the current user (either by user_id or email)
        error_reports = ErrorReport.objects.filter(
            Q(reporter_user=request.user) | Q(reporter_email=request.user.email)
        ).order_by('-created_at')
        
        # Pagination
        paginator = Paginator(error_reports, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        print(f"👨‍🎓 User has {error_reports.count()} error reports")
        
        context = {
            'error_reports': page_obj,
            'total_reports': error_reports.count(),
        }
        
        return render(request, 'blog/my_error_reports.html', context)
        
    except Exception as e:
        print(f"❌ Error loading user error reports: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, 'שגיאה בטעינת הדיווחים שלך')
        return render(request, 'blog/my_error_reports.html', {'error_message': str(e)})
@user_passes_test(lambda u: u.is_staff)
def error_report_list(request):
    """List all error reports for staff members"""
    try:
        print(f"📋 Loading error report list for staff user: {request.user.username}")
        
        # Get filter parameters
        status_filter = request.GET.get('status', '')
        priority_filter = request.GET.get('priority', '')
        type_filter = request.GET.get('type', '')
        search_query = request.GET.get('search', '')
        
        # Start with all error reports
        error_reports = ErrorReport.objects.all().select_related('reporter_user', 'assigned_to')
        
        # Apply filters
        if status_filter:
            error_reports = error_reports.filter(status=status_filter)
        
        if priority_filter:
            error_reports = error_reports.filter(priority=priority_filter)
        
        if type_filter:
            error_reports = error_reports.filter(error_type=type_filter)
        
        if search_query:
            error_reports = error_reports.filter(
                Q(reporter_name__icontains=search_query) |
                Q(reporter_email__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # Order by priority and creation date
        priority_order = ['critical', 'high', 'medium', 'low']
        case_statements = " ".join([f"WHEN '{p}' THEN {i}" for i, p in enumerate(priority_order)])
        error_reports = error_reports.extra(
            select={'priority_order': f"CASE priority {case_statements} END"}
        ).order_by('priority_order', '-created_at')
        
        # Pagination
        paginator = Paginator(error_reports, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Get statistics
        stats = get_error_report_stats()
        
        print(f"📊 Found {error_reports.count()} error reports")
        
        context = {
            'error_reports': page_obj,
            'stats': stats,
            'status_filter': status_filter,
            'priority_filter': priority_filter,
            'type_filter': type_filter,
            'search_query': search_query,
            'error_type_choices': ErrorReport.ERROR_TYPE_CHOICES,
            'priority_choices': ErrorReport.PRIORITY_CHOICES,
            'status_choices': ErrorReport.STATUS_CHOICES,
        }
        
        return render(request, 'blog/error_report_list.html', context)
        
    except Exception as e:
        print(f"❌ Error loading error report list: {str(e)}")
        import traceback
        traceback.print_exc()
# ============================================================================
# HELPER AND UTILITY VIEWS
# ============================================================================
# ============================================================================
# UPDATE STATUS VIEWS FOR SCHEDULE AND PERSONAL REQUESTS
# ============================================================================


@login_required
def get_subjects_by_department(request):
    """API endpoint to get subjects filtered by the user's department"""
    try:
        user_department = request.user.department
        subjects = Subject.objects.filter(
            department=user_department
        ).select_related('lecturer').order_by('name')
        
        subjects_data = []
        for subject in subjects:
            # Get lecturer name with proper fallback
            lecturer_first_name = getattr(subject.lecturer, 'first_name', '') or ''
            lecturer_last_name = getattr(subject.lecturer, 'last_name', '') or ''
            
            if lecturer_first_name or lecturer_last_name:
                lecturer_name = f"{lecturer_first_name} {lecturer_last_name}".strip()
            else:
                lecturer_name = getattr(subject.lecturer, 'username', 'לא זמין')
                
            subjects_data.append({
                'name': subject.name,
                'lecturer_name': lecturer_name,
                'lecturer_id': subject.lecturer.id if subject.lecturer else None
            })
        
        return JsonResponse({'subjects': subjects_data})
        
    except Exception as e:
        print(f"Error in get_subjects_by_department: {str(e)}")
        return JsonResponse({'subjects': []})

@login_required
def create_lecturer_subjects(request):
    """Helper function to create subjects for a lecturer"""
    if not request.user.is_lecturer:
        return redirect('blog-home')
    
    # Create some default subjects for this lecturer
    default_subjects = [
        'מבני נתונים',
        'אלגוריתמים', 
        'תכנות מונחה עצמים',
        'מתמטיקה בדידה',
        'מערכות הפעלה'
    ]
    
    created_count = 0
    for subject_name in default_subjects:
        subject, created = Subject.objects.get_or_create(
            name=subject_name,
            department=request.user.department,
            lecturer=request.user
        )
        if created:
            created_count += 1
    
    messages.success(request, f'נוצרו {created_count} קורסים חדשים עבורך!')
    return redirect('lecturer_dashboard')

# ============================================================================
# DEBUGGING VIEWS (Remove in production)
# ============================================================================

@login_required
def debug_subjects(request):
    """Debug view to check subjects"""
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    print("🔍 DEBUG SUBJECTS VIEW")
    print("=" * 25)
    
    user_dept = request.user.department
    print(f"User: {request.user.username}")
    print(f"Department: {user_dept}")
    
    # Check all subjects
    all_subjects = Subject.objects.all()
    print(f"Total subjects in DB: {all_subjects.count()}")
    
    for subject in all_subjects:
        print(f"  📚 {subject.name} - 🏢 {subject.department} - 👨‍🏫 {subject.lecturer.username}")
    
    # Check subjects for user's department
    dept_subjects = Subject.objects.filter(department=user_dept)
    print(f"Subjects in {user_dept}: {dept_subjects.count()}")
    
    # Return JSON response
    return JsonResponse({
        'user': request.user.username,
        'department': user_dept,
        'total_subjects': all_subjects.count(),
        'user_dept_subjects': dept_subjects.count(),
        'subjects': [
            {
                'name': s.name,
                'department': s.department,
                'lecturer': s.lecturer.username
            } for s in dept_subjects
        ]
    })

@login_required
def fix_subject_departments(request):
    """Fix existing subjects to use Hebrew department names"""
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    dept_mapping = {
        'sw_engineering': 'הנדסת תוכנה',
        'computer_science': 'מדעי המחשב',
        'electronic_engineering': 'הנדסת אלקטרוניקה'
    }
    
    updated_count = 0
    
    for old_dept, new_dept in dept_mapping.items():
        subjects_to_update = Subject.objects.filter(department=old_dept)
        count = subjects_to_update.count()
        
        if count > 0:
            subjects_to_update.update(department=new_dept)
            updated_count += count
            print(f"✅ Updated {count} subjects from '{old_dept}' to '{new_dept}'")
    
    return JsonResponse({
        'status': 'success',
        'message': f'Updated {updated_count} subjects to Hebrew department names'
    })

@login_required
def debug_subjects_detailed(request):
    """Detailed debugging for subject loading issues"""
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    debug_info = {
        'user_info': {
            'username': request.user.username,
            'department': getattr(request.user, 'department', 'NO DEPARTMENT'),
            'is_student': getattr(request.user, 'is_student', 'NO ATTR'),
            'is_lecturer': getattr(request.user, 'is_lecturer', 'NO ATTR'),
        },
        'all_subjects': [],
        'department_analysis': {},
    }
    
    # Get all subjects
    all_subjects = Subject.objects.all().select_related('lecturer')
    
    for subj in all_subjects:
        debug_info['all_subjects'].append({
            'name': subj.name,
            'department': subj.department,
            'lecturer_username': subj.lecturer.username if subj.lecturer else 'NO LECTURER',
            'lecturer_first_name': getattr(subj.lecturer, 'first_name', '') if subj.lecturer else '',
            'lecturer_last_name': getattr(subj.lecturer, 'last_name', '') if subj.lecturer else '',
        })
    
    # Analyze departments
    unique_departments = set(subj.department for subj in all_subjects if subj.department)
    debug_info['department_analysis'] = {
        'unique_departments': list(unique_departments),
        'total_subjects': all_subjects.count(),
        'department_counts': {}
    }
    
    for dept in unique_departments:
        count = all_subjects.filter(department=dept).count()
        debug_info['department_analysis']['department_counts'][dept] = count
    
    return JsonResponse(debug_info, ensure_ascii=False)

# ============================================================================
# LEGACY SUPPORT VIEWS (if needed)
# ============================================================================

