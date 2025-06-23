from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Profile 
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.core.exceptions import ValidationError

# forms.py
class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    is_student = forms.BooleanField(required=False)
    is_lecturer = forms.BooleanField(required=False)
    is_secretary = forms.BooleanField(required=False)

    department = forms.ChoiceField(
        choices=[('', '--- Select Department ---')] + User.DEPARTMENT_CHOICES, 
        required=False
    )
    year = forms.ChoiceField(
        choices=[('', '--- Select Year ---')] + User.YEAR_CHOICES, 
        required=False
    )
    
    # Add courses field
    courses = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'is_student', 'is_lecturer', 'department', 'year']

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        is_student = cleaned_data.get('is_student')
        is_lecturer = cleaned_data.get('is_lecturer')
        department = cleaned_data.get('department')
        year = cleaned_data.get('year')
        courses = cleaned_data.get('courses')
        
        if not (is_student or is_lecturer):
            raise forms.ValidationError("Please choose one role.")
        
        if is_student and is_lecturer:
            raise forms.ValidationError("You can't choose both roles.")
        
        if is_lecturer and email and not email.endswith('@sce.ac.il'):
            raise forms.ValidationError("Lecturers must register with an email ending in @sce.ac.il")
        
        if is_student and email and not email.endswith('@ac.sce.ac.il'):
            raise forms.ValidationError("Students must register with an email ending in @ac.sce.ac.il")
        
        if (is_student or is_lecturer) and not department:
            raise forms.ValidationError("Please select a department.")
        
        if is_student and not year:
            raise forms.ValidationError("Students must select their year.")
        
        if is_lecturer and year:
            cleaned_data['year'] = ''
        
        # Validate courses for lecturers
        if is_lecturer:
            if not courses:
                raise forms.ValidationError("מרצים חייבים להזין לפחות קורס אחד.")
            
            # Parse courses (they come as JSON string)
            try:
                import json
                courses_list = json.loads(courses)
                if not courses_list or not any(course.strip() for course in courses_list):
                    raise forms.ValidationError("מרצים חייבים להזין לפחות קורס אחד.")
            except (json.JSONDecodeError, TypeError):
                raise forms.ValidationError("שגיאה בעיבוד רשימת הקורסים.")
                
        return cleaned_data
    
class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User  
        fields = ['username', 'email', 'department', 'year']  

    def clean_email(self):
        email = self.cleaned_data.get('email')
        user = self.instance

        if user.is_student and not email.endswith('@ac.sce.ac.il'):
            raise forms.ValidationError("Students must use an email ending with @ac.sce.ac.il")

        if user.is_lecturer and not email.endswith('@sce.ac.il'):
            raise forms.ValidationError("Lecturers must use an email ending with @sce.ac.il")

        return email
    
    def clean(self):
        cleaned_data = super().clean()
        user = self.instance
        year = cleaned_data.get('year')
        
     
        if user.is_lecturer and year:
            cleaned_data['year'] = ''
            
       
        if user.is_student and not year:
            raise forms.ValidationError("Students must have a year selected.")
            
        return cleaned_data

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = []  



#password :

class PasswordManagementForm(forms.Form):
    def __init__(self, user=None, stage='change', *args, **kwargs):
        self.user = user
        self.stage = stage
        super().__init__(*args, **kwargs)
        
        if stage == 'change' and user is not None:
            self.fields['old_password'] = forms.CharField(
                label='Current Password',
                widget=forms.PasswordInput(attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter current password',
                    'autocomplete': 'current-password'
                }),
                required=True
            )
            self.fields['new_password1'] = forms.CharField(
                label='New Password',
                widget=forms.PasswordInput(attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter new password',
                    'autocomplete': 'new-password'
                }),
                required=True,
                help_text="Your password must contain at least 8 characters."
            )
            self.fields['new_password2'] = forms.CharField(
                label='Confirm Password',
                widget=forms.PasswordInput(attrs={
                    'class': 'form-control',
                    'placeholder': 'Confirm new password',
                    'autocomplete': 'new-password'
                }),
                required=True
            )
        
        elif stage == 'request_code':
            self.fields['email'] = forms.EmailField(
                label='Email Address',
                widget=forms.EmailInput(attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter your registered email',
                    'autocomplete': 'email'
                }),
                required=True
            )
        
        elif stage == 'reset':
            self.fields['code'] = forms.CharField(
                label='Verification Code',
                max_length=6,
                min_length=6,
                widget=forms.TextInput(attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter 6-digit code',
                    'autocomplete': 'off'
                }),
                required=True
            )
            self.fields['new_password1'] = forms.CharField(
                label='New Password',
                widget=forms.PasswordInput(attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter new password',
                    'autocomplete': 'new-password'
                }),
                required=True
            )
            self.fields['new_password2'] = forms.CharField(
                label='Confirm Password',
                widget=forms.PasswordInput(attrs={
                    'class': 'form-control',
                    'placeholder': 'Confirm new password',
                    'autocomplete': 'new-password'
                }),
                required=True
            )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            raise ValidationError("No account found with this email address.")
        
        user = User.objects.get(email=email)
        if hasattr(user, 'is_student') and user.is_student and not email.endswith('@ac.sce.ac.il'):
            raise ValidationError("Student accounts must use @ac.sce.ac.il email")
        if hasattr(user, 'is_lecturer') and user.is_lecturer and not email.endswith('@sce.ac.il'):
            raise ValidationError("Lecturer accounts must use @sce.ac.il email")
        
        return email

    def clean_code(self):
        if self.stage != 'reset':
            return None
            
        code = self.cleaned_data.get('code')
        if not code or len(code) != 6:
            raise ValidationError("Invalid verification code format")
        
        return code

    def clean(self):
        cleaned_data = super().clean()
        
        if self.stage in ['change', 'reset']:
            new_password1 = cleaned_data.get('new_password1')
            new_password2 = cleaned_data.get('new_password2')
            
            if new_password1 and new_password2 and new_password1 != new_password2:
                raise ValidationError("The two password fields didn't match.")
            
            if self.stage == 'change':
                old_password = cleaned_data.get('old_password')
                if old_password and self.user and not self.user.check_password(old_password):
                    raise ValidationError("Your current password was entered incorrectly.")
        
        return cleaned_data

    def save(self):
        if self.stage == 'change':
            self.user.set_password(self.cleaned_data['new_password1'])
            self.user.save()
            return self.user
        return None

class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
                'placeholder': f'Enter your {field.replace("_", " ")}'
            })
