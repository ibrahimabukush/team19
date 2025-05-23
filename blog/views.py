from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
User = get_user_model()
from django.utils import timezone
from django.conf import settings

from dotenv import load_dotenv
from pathlib import Path
import os
import json
import base64
import traceback

from openai import OpenAI

from .models import ChatHistory, StudentRequest
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
        
        # Determine who to assign the request to
        assigned_to = None
        
        # Check if this is a lecturer-related request
        lecturer_request_types = ['academic_appeal', 'exam_review']
        
        if request_type in lecturer_request_types and subject_name:
            # Map department for finding the subject
            department_mapping = {
                'sw_engineering': 'Software Engineering',
                'cs_engineering': 'Computer Science',
                'ee_engineering': 'Electronic Engineering',
                '': 'Software Engineering',  # Default fallback
                # Add variations if needed
                'computer_science': 'Computer Science',
                'electronic_engineering': 'Electronic Engineering',
                'software_engineering': 'Software Engineering',
            }
            
            user_department = request.user.department
            subject_department = department_mapping.get(user_department, user_department)
            
            # Find the lecturer for the selected subject
            try:
                subject_obj = Subject.objects.get(
                    name=subject_name, 
                    department=subject_department
                )
                assigned_to = subject_obj.lecturer
            except Subject.DoesNotExist:
                messages.error(request, 'הקורס שנבחר לא נמצא במחלקה שלך.')
                return JsonResponse({'status': 'error', 'message': 'הקורס שנבחר לא נמצא במחלקה שלך.'})
        else:
            # Assign to department secretary
            department = request.user.department
            try:
                assigned_to = User.objects.get(
                    is_secretary=True, 
                    department=department
                )
            except User.DoesNotExist:
                messages.error(request, 'לא נמצאה מזכירה למחלקה שלך.')
                return JsonResponse({'status': 'error', 'message': 'לא נמצאה מזכירה למחלקה שלך.'})
        
        # Create the request
        academic_request = AcademicRequest.objects.create(
            student=request.user,
            assigned_to=assigned_to,
            subject=subject_name if subject_name else '',
            request_type=request_type,
            request_text=description,
            attachment=attachment,
            status='pending'
        )
        
        messages.success(request, 'הבקשה שלך הוגשה בהצלחה!')
        return JsonResponse({'status': 'success', 'message': 'הבקשה הוגשה בהצלחה'})
    
    # GET request - show the form
    # Handle department mapping for GET requests too
    department_mapping = {
        'sw_engineering': 'Software Engineering',
        'cs_engineering': 'Computer Science',
        'ee_engineering': 'Electronic Engineering',
        '': 'Software Engineering',  # Default fallback
        # Add variations if needed
        'computer_science': 'Computer Science',
        'electronic_engineering': 'Electronic Engineering',
        'software_engineering': 'Software Engineering',
    }
    
    user_department = request.user.department
    subject_department = department_mapping.get(user_department, user_department)
    
    subjects = Subject.objects.filter(department=subject_department).order_by('name')
    
    return render(request, 'blog/academic_requests.html', {'subjects': subjects})
@login_required
def get_lecturer(request):
    subject_name = request.GET.get('subject')
    try:
        # Filter by department to ensure security
        subject = Subject.objects.get(
            name=subject_name, 
            department=request.user.department
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
# @login_required
# def lecturer_dashboard(request):
#     if not request.user.is_lecturer:
#         return redirect('home')
    
#     # Get all requests assigned to this lecturer
#     requests = AcademicRequest.objects.filter(
#         assigned_to=request.user
#     ).order_by('-created_at')
    
#     return render(request, 'users/lecturer_dashboard.html', {'requests': requests})
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

# @login_required
# def secretary_dashboard(request):
#     if not request.user.is_secretary:
#         return redirect('home')
    
#     # Get all requests assigned to this secretary
#     requests = AcademicRequest.objects.filter(
#         assigned_to=request.user
#     ).order_by('-created_at')
    
#     return render(request, 'secretary_dashboard.html', {'requests': requests})

@login_required
def get_lecturer(request):
    subject_name = request.GET.get('subject')
    try:
        subject = Subject.objects.get(name=subject_name)
        return JsonResponse({
            'lecturer_name': f"{subject.lecturer.first_name} {subject.lecturer.last_name}" 
            if subject.lecturer.first_name 
            else subject.lecturer.username
        })
    except Subject.DoesNotExist:
        return JsonResponse({'lecturer_name': None})
@login_required
def tracking(request):
    user_requests = AcademicRequest.objects.filter(student=request.user)

    # Annotate if deadline passed
    for req in user_requests:
        req.is_past_deadline = False
        if req.status == "need_update" and req.update_deadline:
            req.is_past_deadline = timezone.now() > req.update_deadline

    return render(request, 'blog/tracking.html', {'requests': user_requests})

from .models import ScheduleRequest

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
        return redirect('blog-home')
    
    # Get today's date
    today = timezone.now().date()
    
    # Get quick stats for today
    today_requests = AcademicRequest.objects.filter(
        assigned_to=request.user,
        created_at__date=today
    ).count()
    
    # Get pending requests count
    pending_requests = AcademicRequest.objects.filter(
        assigned_to=request.user,
        status='pending'
    ).count()
    
    # Get urgent requests (older than 3 days and still pending)
    urgent_requests = AcademicRequest.objects.filter(
        assigned_to=request.user,
        status='pending',
        created_at__lte=timezone.now() - timedelta(days=3)
    ).count()
    
    # Get recent 5 requests
    recent_requests = AcademicRequest.objects.filter(
        assigned_to=request.user
    ).order_by('-created_at')[:5]
    
    # Updated department name mapping to handle all variations
    department_names = {
        'sw_engineering': 'הנדסת תוכנה',
        'cs_engineering': 'מדעי המחשב',
        'ee_engineering': 'הנדסת אלקטרוניקה',
        'electronic_engineering': 'הנדסת אלקטרוניקה',
        'computer_science': 'מדעי המחשב',
        'software_engineering': 'הנדסת תוכנה',
    }
    
    context = {
        'department_name': department_names.get(request.user.department, request.user.department),
        'today_requests': today_requests,
        'pending_requests': pending_requests,
        'urgent_requests': urgent_requests,
        'recent_requests': recent_requests,
        'current_time': timezone.now(),
    }
    
    return render(request, 'blog/secretary_home.html', context)

@login_required
def secretary_dashboard(request):
    # Check if user is a secretary
    if not request.user.is_secretary:
        messages.error(request, 'הגישה מותרת למזכירות בלבד.')
        return redirect('blog-home')
    
    # Get all requests assigned to this secretary
    all_requests = AcademicRequest.objects.filter(
        assigned_to=request.user
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
    
    # Updated department name mapping
    department_names = {
        'sw_engineering': 'הנדסת תוכנה',
        'cs_engineering': 'מדעי המחשב',
        'ee_engineering': 'הנדסת אלקטרוניקה',
        'electronic_engineering': 'הנדסת אלקטרוניקה',
        'computer_science': 'מדעי המחשב',
        'software_engineering': 'הנדסת תוכנה',
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


@login_required
def academic_request(request):
    subjects = LecturerProfile.objects.exclude(subject__isnull=True).exclude(subject__exact='').values_list('subject', flat=True).distinct()
    return render(request, 'blog/academic_request.html', {
        'subjects': subjects
    })
@login_required
def schedule_request(request):
    return render(request, 'blog/schedule_requests.html')

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from users.models import LecturerProfile
from .models import AcademicRequest

@login_required
def lecturer_requests_view(request):
    user = request.user

    # Check if user is a lecturer
    if not user.is_authenticated or not hasattr(user, 'lecturerprofile'):
        return render(request, 'blog/not_authorized.html')

    subject = user.lecturerprofile.subject

    # Get all requests that match the subject this lecturer teaches
    requests = AcademicRequest.objects.filter(subject=subject)

    return render(request, 'blog/lecturer_requests.html', {
        'requests': requests,
        'subject': subject,
    })
#----------------------------------------------------------------------------------$
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from .models import AcademicRequest

@login_required
def secretary_dashboard(request):
    # Check if user is a secretary
    if not request.user.is_secretary:
        messages.error(request, 'הגישה מותרת למזכירות בלבד.')
        return redirect('blog-home')
    
    # Get all requests assigned to this secretary
    all_requests = AcademicRequest.objects.filter(
        assigned_to=request.user
    ).order_by('-created_at')
    
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
    
    # Department name mapping
    department_names = {
         'sw_engineering': 'הנדסת תוכנה',
    'cs_engineering': 'מדעי המחשב',
    'ee_engineering': 'הנדסת אלקטרוניקה',
    'Computer Science': 'מדעי המחשב',
    'Software Engineering': 'הנדסת תוכנה',
    'Electronic Engineering': 'הנדסת אלקטרוניקה',
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
    }
    
    return render(request, 'blog/secretary_dashboard.html', context)

def technicalmanagement(request):
    return render(request, 'blog/technicalmanagement.html')

@login_required
def update_request_status(request, request_id):
    if not request.user.is_secretary:
        messages.error(request, 'הגישה מותרת למזכירות בלבד.')
        return redirect('blog-home')
    
    if request.method == 'POST':
        academic_request = get_object_or_404(AcademicRequest, id=request_id)
        new_status = request.POST.get('status')
        
        academic_request.status = new_status
        academic_request.save()
        
        messages.success(request, 'סטטוס הבקשה עודכן בהצלחה.')
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})
@login_required
def get_subjects_by_department(request):
    user = request.user
    if user.is_student:
        subjects = Subject.objects.filter(department=user.department)
        data = [
            {
                "name": subject.name,
                "lecturer": subject.lecturer.get_full_name() or subject.lecturer.username
            } for subject in subjects
        ]
        return JsonResponse(data, safe=False)
    return JsonResponse({"error": "Unauthorized"}, status=403)

@login_required
def secretary_request_detail(request, request_id):
    if not request.user.is_secretary:
        messages.error(request, 'הגישה מותרת למזכירות בלבד.')
        return redirect('blog-home')
    
    academic_request = get_object_or_404(AcademicRequest, id=request_id, assigned_to=request.user)
    
    context = {
        'request': academic_request,
    }
    
    return render(request, 'blog/secretary_request_detail.html', context)

    