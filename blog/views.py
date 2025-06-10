

from datetime import timedelta
from itertools import count
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings

from dotenv import load_dotenv
from pathlib import Path
import os
import json
import base64
import traceback

from openai import OpenAI

from .models import ChatHistory, ScheduleRequest, StudentRequest
from users.models import LecturerProfile
import users.views

# views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from users.models import Subject
from django.contrib.auth import get_user_model
from .models import AcademicRequest, Post, ChatHistory, StudentRequest

User = get_user_model()

# blog/views.py
# blog/views.py

@login_required
def submit_request(request):
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
        
        # Create the request WITHOUT assigned_to
        try:
            academic_request = AcademicRequest.objects.create(
                student=request.user,
                # הסר את assigned_to מכאן
                subject=subject_name if subject_name else '',
                request_type=request_type,
                request_text=description,
                attachment=attachment,
                status='pending'
            )
            
            messages.success(request, 'הבקשה שלך הוגשה בהצלחה!')
            return JsonResponse({'status': 'success', 'message': 'הבקשה הוגשה בהצלחה'})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'שגיאה: {str(e)}'})
    
    # GET request - show the form
    subjects = Subject.objects.all()
    return render(request, 'blog/academic_request.html', {'subjects': subjects})
@login_required 
def update_request_status(request, request_id):
    if request.method == 'POST':
        try:
            academic_request = get_object_or_404(AcademicRequest, id=request_id)
            new_status = request.POST.get('status')
            
            # בדוק שהסטטוס תקין
            valid_statuses = ['pending', 'in_progress', 'need_update', 'approved', 'rejected']
            if new_status in valid_statuses:
                academic_request.status = new_status
                academic_request.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'סטטוס עודכן בהצלחה'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'סטטוס לא תקין'
                })
                
        except AcademicRequest.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'בקשה לא נמצאה'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def get_subjects_by_department(request):
    """
    API endpoint to get subjects filtered by the user's department
    """
    user_department = request.user.department
    subjects = Subject.objects.filter(department=user_department).order_by('name')
    
    subjects_data = []
    for subject in subjects:
        lecturer_name = f"{subject.lecturer.first_name} {subject.lecturer.last_name}"
        if not subject.lecturer.first_name:
            lecturer_name = subject.lecturer.username
            
        subjects_data.append({
            'name': subject.name,
            'lecturer_name': lecturer_name,
            'lecturer_id': subject.lecturer.id
        })
    
    return JsonResponse({'subjects': subjects_data})

@login_required
def get_lecturer(request):
    """
    API endpoint to get lecturer information for a specific subject
    """
    subject_name = request.GET.get('subject')
    user_department = request.user.department
    
    try:
        # Filter by department to ensure security
        subject = Subject.objects.get(
            name=subject_name, 
            department=user_department
        )
        
        lecturer_name = f"{subject.lecturer.first_name} {subject.lecturer.last_name}"
        if not subject.lecturer.first_name:
            lecturer_name = subject.lecturer.username
        
        return JsonResponse({
            'lecturer_name': lecturer_name,
            'lecturer_id': subject.lecturer.id
        })
    except Subject.DoesNotExist:
        return JsonResponse({'lecturer_name': None, 'lecturer_id': None})

# Rest of the views remain the same...
def home(request):
    if request.user.is_authenticated:
        if request.user.is_secretary:
            return redirect('secretary-dashboard')
    
    # Define posts (or get them from your model)
    posts = Post.objects.all().order_by('-date_posted') if 'Post' in globals() else []
    
    return render(request, 'blog/home.html', {'posts': posts})

def about(request):
    return render(request, 'blog/about.html', {'title': 'About'})

def services(request):
    return render(request, 'blog/services.html', {'title': 'Services'})

def contact(request):
    return render(request, 'blog/contact.html', {'title': 'Contact'})


@login_required
def academic_request(request):
    subjects = LecturerProfile.objects.exclude(subject__isnull=True).exclude(subject__exact='').values_list('subject', flat=True).distinct()
    return render(request, 'blog/academic_request.html', {
        'subjects': subjects
    })
@login_required
def schedule_request(request):
    return render(request, 'blog/schedule_requests.html')
@login_required
def tracking(request):
    user_requests = AcademicRequest.objects.filter(student=request.user)

    # Annotate if deadline passed
    for req in user_requests:
        req.is_past_deadline = False
        if req.status == "need_update" and req.update_deadline:
            req.is_past_deadline = timezone.now() > req.update_deadline

    return render(request, 'blog/tracking.html', {'requests': user_requests})

@login_required
def schedule_request_view(request):
    """View for displaying the schedule request form"""
    return render(request, 'blog/schedule_request.html')

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

@login_required
def secretary_dashboard(request):
    # Check if user is a secretary
    if not request.user.is_secretary:
        messages.error(request, 'הגישה מותרת למזכירות בלבד.')
        return redirect('blog-home')
    
    # Get requests only from students in the same department as this secretary
    all_requests = AcademicRequest.objects.filter(
        student__department=request.user.department
    ).order_by('-created_at')
    
    # Debug logging
    print(f"Secretary: {request.user.username}, Department: {request.user.department}")
    print(f"Total requests found: {all_requests.count()}")
    
    # Filter by status if provided
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        filtered_requests = all_requests.filter(status=status_filter)
    else:
        filtered_requests = all_requests
    
    # Get statistics
    stats = {
        'total': all_requests.count(),
        'pending': all_requests.filter(status='pending').count(),
        'in_progress': all_requests.filter(status='in_progress').count(),
        'need_update': all_requests.filter(status='need_update').count(),
        'approved': all_requests.filter(status='approved').count(),
        'rejected': all_requests.filter(status='rejected').count(),
    }
    
    # Get requests by type
    from django.db.models import Count
    request_types_stats = all_requests.values('request_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Format request types for display
    type_display_names = {
        'enrollment_confirmation': 'אישורי רישום או ציונים',
        'academic_appeal': 'ערעורים אקדמיים',
        'exam_review': 'בקשות לבדיקת מבחנים',
        'schedule_change': 'שינוי מערכת שעות',
        'administrative': 'בקשות מנהליות',
    }
    
    for stat in request_types_stats:
        stat['display_name'] = type_display_names.get(stat['request_type'], stat['request_type'])
    
    # Get urgent requests (pending for more than 3 days)
    three_days_ago = timezone.now() - timedelta(days=3)
    urgent_requests = all_requests.filter(
        status='pending',
        created_at__lte=three_days_ago
    )
    
    # Department names mapping
    department_names = {
        'מדעי המחשב': 'מדעי המחשב',
        'הנדסת תוכנה': 'הנדסת תוכנה', 
        'הנדסת אלקטרוניקה': 'הנדסת אלקטרוניקה',
        'sw_engineering': 'הנדסת תוכנה',
        'cs_engineering': 'מדעי המחשב',
        'ee_engineering': 'הנדסת אלקטרוניקה',
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
    }
    
    return render(request, 'blog/secretary_dashboard.html', context)

# @require_POST
# @csrf_exempt  # For testing only; use proper CSRF protection in production
# def save_pdf_to_profile(request):
#     """
#     Save a generated PDF to the user's profile.
#     Expects a JSON payload with studentId, studentName, pdfData, documentType, and semester.
#     """
#     try:
#         data = json.loads(request.body)
#         student_id = data.get('studentId')
#         student_name = data.get('studentName')
#         pdf_data = data.get('pdfData')
#         document_type = data.get('documentType')
#         semester = data.get('semester')
        
#         # Validate required fields
#         if not all([student_id, student_name, pdf_data, document_type, semester]):
#             return JsonResponse({'status': 'error', 'message': 'Missing required fields'}, status=400)
        
#         # Extract base64 data from data URI
#         pdf_base64 = pdf_data.split(',')[1] if ',' in pdf_data else pdf_data
#         pdf_bytes = base64.b64decode(pdf_base64)
        
#         # Create directory for user if it doesn't exist
#         user_directory = os.path.join(settings.MEDIA_ROOT, 'user_documents', f'user_{request.user.id}')
#         os.makedirs(user_directory, exist_ok=True)
        
#         # Create filename
#         filename = f"{document_type}_{student_id}_{semester.replace(' ', '_')}.pdf"
#         file_path = os.path.join(user_directory, filename)
        
#         # Save the file
#         with open(file_path, 'wb') as f:
#             f.write(pdf_bytes)
        
#         # Save reference to database
#         # In a real implementation, you would create a model instance here
#         # Example:
#         # UserDocument.objects.create(
#         #     user=request.user,
#         #     document_type=document_type,
#         #     semester=semester,
#         #     file_path=file_path,
#         #     filename=filename
#         # )
        
#         return JsonResponse({
#             'status': 'success',
#             'message': 'Document saved successfully',
#             'file_path': file_path,
#             'filename': filename
#         })
        
#     except Exception as e:
#         return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
 
@login_required
def chat_history(request):
    history = ChatHistory.objects.filter(username=request.user.username).order_by('-timestamp')
    return render(request, 'blog/chat_history.html', {'history': history})

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


posts = [
    {
        'author': 'CoreyMS',
        'title': 'Blog Post 1',
        'content': 'First post content',
        'date_posted': 'August 27, 2018'
    },
    {
        'author': 'Jane Doe',
        'title': 'Blog Post 2',
        'content': 'Second post content',
        'date_posted': 'August 28, 2018'
    }
]



@csrf_exempt
def chatbot_response(request):
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
- ✅ Keywords: proof I’m a student, enrollment document, certificate, official paper, confirmation letter, proof of studies, student status, for scholarship, get official doc
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
            
           
            from .models import ChatHistory
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


def technicalmanagement(request):
    """
    Display the technical management error reporting form
    """
    return render(request, 'blog/technicalmanagement.html')

@require_POST
def submit_error_report(request):
    """
    Handle the submission of error reports
    """
    try:
        # Extract form data
        reporter_name = request.POST.get('name', '').strip()
        reporter_email = request.POST.get('email', '').strip()
        error_type = request.POST.get('errorType', '')
        error_description = request.POST.get('description', '').strip()
        urgency = request.POST.get('urgency', 'medium')
        error_media = request.FILES.get('errorMedia')
        
        # Validate required fields
        if not all([reporter_name, reporter_email, error_type, error_description]):
            return JsonResponse({
                'success': False,
                'message': 'נא למלא את כל השדות הנדרשים'
            }, status=400)
        
        # Validate email format
        import re
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_pattern, reporter_email):
            return JsonResponse({
                'success': False,
                'message': 'נא להזין כתובת אימייל תקינה'
            }, status=400)
        
        # Validate file size if media is uploaded
        if error_media and error_media.size > 20 * 1024 * 1024:  # 20MB limit
            return JsonResponse({
                'success': False,
                'message': 'גודל הקובץ המקסימלי המותר הוא 20MB'
            }, status=400)
        
        # Create ErrorReport instance
        # Note: You'll need to uncomment this when you add the model to blog/models.py
        """
        error_report = ErrorReport.objects.create(
            reporter_name=reporter_name,
            reporter_email=reporter_email,
            error_type=error_type,
            error_description=error_description,
            urgency=urgency,
            error_media=error_media
        )
        """
        
        # For now, just log the data (remove this when using the actual model)
        print(f"Error Report Submitted:")
        print(f"Name: {reporter_name}")
        print(f"Email: {reporter_email}")
        print(f"Type: {error_type}")
        print(f"Description: {error_description}")
        print(f"Urgency: {urgency}")
        print(f"Media: {error_media.name if error_media else 'None'}")
        
        # Return success response
        return JsonResponse({
            'success': True,
            'message': 'הדיווח נשלח בהצלחה! הצוות הטכני יטפל בתקלה במהירות האפשרית.'
        })
        
    except Exception as e:
        print(f"Error in submit_error_report: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'אירעה שגיאה בשליחת הדיווח. נא לנסות שוב.'
        }, status=500)

# Additional view for listing error reports (for admin/technical team)
def error_reports_list(request):
    """
    Display list of all error reports (for technical team)
    """
    # Note: Uncomment when ErrorReport model is added
    """
    if not request.user.is_staff:
        return redirect('blog-home')
    
    reports = ErrorReport.objects.all().order_by('-created_at')
    context = {
        'reports': reports,
        'pending_count': reports.filter(status='pending').count(),
        'in_progress_count': reports.filter(status='in_progress').count(),
    }
    return render(request, 'blog/error_reports_list.html', context)
    """
    
    # Temporary placeholder
    return render(request, 'blog/error_reports_list.html', {
        'reports': [],
        'pending_count': 0,
        'in_progress_count': 0,
    })

# View for updating error report status (for technical team)
@require_POST
def update_error_report_status(request, report_id):
    """
    Update the status of an error report
    """
    try:
        # Note: Uncomment when ErrorReport model is added
        """
        if not request.user.is_staff:
            return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
        
        report = ErrorReport.objects.get(id=report_id)
        new_status = request.POST.get('status')
        admin_notes = request.POST.get('admin_notes', '')
        
        if new_status in dict(ErrorReport.STATUS_CHOICES):
            report.status = new_status
            if admin_notes:
                report.admin_notes = admin_notes
            report.assigned_to = request.user
            report.save()
            
            return JsonResponse({
                'success': True,
                'message': 'סטטוס הדיווח עודכן בהצלחה'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'סטטוס לא תקין'
            }, status=400)
        """
        
        # Temporary placeholder
        return JsonResponse({
            'success': True,
            'message': 'סטטוס הדיווח עודכן בהצלחה (demo mode)'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'שגיאה בעדכון הסטטוס'
        }, status=500)

