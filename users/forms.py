from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Profile 

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