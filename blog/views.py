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


@csrf_exempt
def chatbot_response(request):
    print(f"Request method: {request.method}")
    print(f"POST data: {request.POST}")
    
    if request.method == "POST":
        try:
            user_message = request.POST.get("message", "")
            print(f"User message: {user_message}")
            
            # Set a default username
            username = "Anonymous"
            # If the user is logged in, use their username
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