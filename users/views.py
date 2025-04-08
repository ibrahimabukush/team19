from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm
from .models import Profile
from django.contrib.auth import authenticate, login
from .forms import UserRegisterForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import requires_csrf_token


def register(request):
    msg = None
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            if user.is_student:
                user.is_approved = True  
            user.save()
            msg = "Account created"
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

                # Redirect based on role
                if user.is_student:
                    return redirect('blog-home')
                elif user.is_lecturer:
                    return redirect('lecturer_dashboard')
               

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