from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile
from .models import User
class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    is_student = forms.BooleanField(required=False)
    is_lecturer = forms.BooleanField(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'is_student', 'is_lecturer']

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        is_student = cleaned_data.get('is_student')
        is_lecturer = cleaned_data.get('is_lecturer')

        if not (is_student or is_lecturer):
            raise forms.ValidationError("Please choose one role.")
        if is_student and is_lecturer:
            raise forms.ValidationError("You can't choose both roles.")

        if is_lecturer and email and not email.endswith('@sce.ac.il'):
            raise forms.ValidationError("Lecturers must register with an email ending in @sce.ac.il")

        if is_student and email and not email.endswith('@ac.sce.ac.il'):
            raise forms.ValidationError("Students must register with an email ending in @ac.sce.ac.il")

        return cleaned_data




class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        user = self.instance

        if user.is_student and not email.endswith('@ac.sce.ac.il'):
            raise forms.ValidationError("Students must use an email ending with @ac.sce.ac.il")

        if user.is_lecturer and not email.endswith('@sce.ac.il'):
            raise forms.ValidationError("Lecturers must use an email ending with @sce.ac.il")

        return email



class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = []