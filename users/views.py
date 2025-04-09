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
import random
from django.contrib.auth import get_user_model

User = get_user_model()

def generate_code():
    return str(random.randint(100000, 999999))
def register(request):
    msg = None
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            if user.is_student:
                user.is_approved = True
                user.is_verified = False
                user.verification_code = generate_code()
                user.save()
                login(request, user)

                # Send verification email to student
                send_mail(
                    subject='🔐 Verify Your iStudent Account',
                    message=f'Hi {user.username},\n\nYour verification code is: {user.verification_code}',
                    from_email=None,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                return redirect('verify_account')
            
            # Handle lecturer registration
            elif user.is_lecturer:
                user.save()  # Save the lecturer user before returning
                msg = "Lecturer account created and waiting approval"
                return redirect('login')
    else:
        form = UserRegisterForm()

    return render(request, 'users/register.html', {'form': form, 'msg': msg})



def login_view(request):
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            if user.is_student and not user.is_verified:
                messages.error(request, "Please verify your account first. Check your email for the code.")
            elif user.is_lecturer and not user.is_approved:
                messages.error(request, "Lecturer account is awaiting admin approval.")
            else:
                login(request, user)

                # Send login email
                send_mail(
                    subject='🔐 New Login Detected',
                    message=f'Hi {user.username}, you have just logged into your iStudent account.',
                    from_email=None,
                    recipient_list=[user.email],
                    fail_silently=False,
                )

                if user.is_student:
                    return redirect('blog-home')
                elif user.is_lecturer:
                    return redirect('lecturer_dashboard')
                
    return render(request, 'users/login.html', {'form': form})



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


@login_required
def verify_account(request):
    if not request.user.is_student:
        return redirect('blog-home')

    if request.method == 'POST':
        code_entered = request.POST.get('code')
        if code_entered == request.user.verification_code:
            request.user.is_verified = True
            request.user.verification_code = ''
            request.user.save()
            messages.success(request, "✅ Account verified!")
            return redirect('blog-home')
        else:
            messages.error(request, "❌ Incorrect code. Please try again.")

    return render(request, 'users/verify_account.html')