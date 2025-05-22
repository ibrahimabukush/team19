from django.shortcuts import render
from openai import OpenAI
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import os
from dotenv import load_dotenv
from pathlib import Path
import traceback
from django.contrib.auth.decorators import login_required
from .models import ChatHistory
from .models import StudentRequest
import os
import json
import base64
import os
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import JsonResponse
import users.views
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.shortcuts import render
from users.models import LecturerProfile
from django.utils import timezone

def submit_request(request):
    if request.method == "POST":
        subject = request.POST.get('subject')
        request_type = request.POST.get('request_type')
        request_text = request.POST.get('request_text')

        # יצירת הבקשה החדשה
        new_request = AcademicRequest(
            student=request.user,  # על פי המודל שלך, אנו משתמשים במשתמש המחובר
            subject=subject,
            request_type=request_type,
            request_text=request_text
        )
        new_request.save()  ## שמירה של הבקשה במסד הנתונים
        return JsonResponse({"message": "Request submitted successfully!"})

    return JsonResponse({"error": "Invalid request"}, status=400)


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


def home(request):
    return render(request, 'blog/home.html', {'posts': posts})

def about(request):
    return render(request, 'blog/about.html', {'title': 'About'})

def services(request):
    return render(request, 'blog/services.html', {'title': 'Services'})

def contact(request):
    return render(request, 'blog/contact.html', {'title': 'Contact'})
from django.shortcuts import render

def technicalmanagement(request):
    return render(request, 'blog/technicalmanagement.html')
    
def contact(request):
    return render(request, 'blog/contact.html')

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
