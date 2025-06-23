from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Profile 
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.core.exceptions import ValidationError

# forms.py
def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add Hebrew labels and placeholders to password fields
        self.fields['username'].label = 'שם משתמש'
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'הזן שם משתמש'
        })
        
        self.fields['password1'].label = 'סיסמה'
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'הזן סיסמה'
        })
        self.fields['password1'].help_text = 'הסיסמה חייבת להכיל לפחות 8 תווים.'
        
        self.fields['password2'].label = 'אימות סיסמה'
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'הזן סיסמה שוב לאימות'
        })
        self.fields['password2'].help_text = 'הזן את אותה סיסמה שוב לאימות.'

# forms.py
class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(
        label='דואר אלקטרוני',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'הזן כתובת דוא"ל'
        })
    )
    full_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'הזן שם מלא'
        }),
        label='שם מלא'
    )
    is_student = forms.BooleanField(required=False)
    is_lecturer = forms.BooleanField(required=False)
    is_secretary = forms.BooleanField(required=False)

    department = forms.ChoiceField(
        choices=[('', '--- בחר מחלקה ---')] + User.DEPARTMENT_CHOICES, 
        required=False,
        label='מחלקה'
    )
    year = forms.ChoiceField(
        choices=[('', '--- בחר שנה ---')] + User.YEAR_CHOICES, 
        required=False,
        label='שנה'
    )
    
    # Add courses field
    courses = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )

    class Meta:
        model = User
        fields = ['username', 'full_name', 'email', 'password1', 'password2', 'is_student', 'is_lecturer', 'department', 'year']

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        full_name = cleaned_data.get('full_name')
        is_student = cleaned_data.get('is_student')
        is_lecturer = cleaned_data.get('is_lecturer')
        department = cleaned_data.get('department')
        year = cleaned_data.get('year')
        courses = cleaned_data.get('courses')
        
        # Validate full name
        if not full_name or not full_name.strip():
            raise forms.ValidationError("שם מלא הוא שדה חובה.")
        
        if not (is_student or is_lecturer):
            raise forms.ValidationError("אנא בחר תפקיד אחד.")
        
        if is_student and is_lecturer:
            raise forms.ValidationError("לא ניתן לבחור בשני תפקידים.")
        
        if is_lecturer and email and not email.endswith('@sce.ac.il'):
            raise forms.ValidationError("מרצים חייבים להירשם עם כתובת דוא\"ל המסתיימת ב-@sce.ac.il")
        
        if is_student and email and not email.endswith('@ac.sce.ac.il'):
            raise forms.ValidationError("סטודנטים חייבים להירשם עם כתובת דוא\"ל המסתיימת ב-@ac.sce.ac.il")
        
        if (is_student or is_lecturer) and not department:
            raise forms.ValidationError("אנא בחר מחלקה.")
        
        if is_student and not year:
            raise forms.ValidationError("סטודנטים חייבים לבחור שנה.")
        
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

    def save(self, commit=True):
        user = super().save(commit=False)
        # Set the full_name field directly since it exists in the model now
        user.full_name = self.cleaned_data['full_name']
        
        if commit:
            user.save()
        return user
    
class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(
        label='דואר אלקטרוני',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'הזן כתובת דוא"ל'
        })
    )
    full_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'הזן שם מלא'
        }),
        label='שם מלא'
    )

    class Meta:
        model = User  
        fields = ['username', 'full_name', 'email', 'department', 'year']
        labels = {
            'username': 'שם משתמש',
            'department': 'מחלקה',
            'year': 'שנה'
        }  

    def clean_email(self):
        email = self.cleaned_data.get('email')
        user = self.instance

        if user.is_student and not email.endswith('@ac.sce.ac.il'):
            raise forms.ValidationError("סטודנטים חייבים להשתמש בכתובת דוא\"ל המסתיימת ב-@ac.sce.ac.il")

        if user.is_lecturer and not email.endswith('@sce.ac.il'):
            raise forms.ValidationError("מרצים חייבים להשתמש בכתובת דוא\"ל המסתיימת ב-@sce.ac.il")

        return email
    
    def clean_full_name(self):
        full_name = self.cleaned_data.get('full_name')
        if not full_name or not full_name.strip():
            raise forms.ValidationError("שם מלא הוא שדה חובה.")
        return full_name.strip()
    
    def clean(self):
        cleaned_data = super().clean()
        user = self.instance
        year = cleaned_data.get('year')
        
        if user.is_lecturer and year:
            cleaned_data['year'] = ''
            
        if user.is_student and not year:
            raise forms.ValidationError("סטודנטים חייבים לבחור שנה.")
            
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
                label='סיסמה נוכחית',
                widget=forms.PasswordInput(attrs={
                    'class': 'form-control',
                    'placeholder': 'הזן סיסמה נוכחית',
                    'autocomplete': 'current-password'
                }),
                required=True
            )
            self.fields['new_password1'] = forms.CharField(
                label='סיסמה חדשה',
                widget=forms.PasswordInput(attrs={
                    'class': 'form-control',
                    'placeholder': 'הזן סיסמה חדשה',
                    'autocomplete': 'new-password'
                }),
                required=True,
                help_text="הסיסמה חייבת להכיל לפחות 8 תווים."
            )
            self.fields['new_password2'] = forms.CharField(
                label='אימות סיסמה',
                widget=forms.PasswordInput(attrs={
                    'class': 'form-control',
                    'placeholder': 'אמת סיסמה חדשה',
                    'autocomplete': 'new-password'
                }),
                required=True
            )
        
        elif stage == 'request_code':
            self.fields['email'] = forms.EmailField(
                label='כתובת דוא"ל',
                widget=forms.EmailInput(attrs={
                    'class': 'form-control',
                    'placeholder': 'הזן את כתובת הדוא"ל הרשומה שלך',
                    'autocomplete': 'email'
                }),
                required=True
            )
        
        elif stage == 'reset':
            self.fields['code'] = forms.CharField(
                label='קוד אימות',
                max_length=6,
                min_length=6,
                widget=forms.TextInput(attrs={
                    'class': 'form-control',
                    'placeholder': 'הזן קוד 6 ספרות',
                    'autocomplete': 'off'
                }),
                required=True
            )
            self.fields['new_password1'] = forms.CharField(
                label='סיסמה חדשה',
                widget=forms.PasswordInput(attrs={
                    'class': 'form-control',
                    'placeholder': 'הזן סיסמה חדשה',
                    'autocomplete': 'new-password'
                }),
                required=True
            )
            self.fields['new_password2'] = forms.CharField(
                label='אימות סיסמה',
                widget=forms.PasswordInput(attrs={
                    'class': 'form-control',
                    'placeholder': 'אמת סיסמה חדשה',
                    'autocomplete': 'new-password'
                }),
                required=True
            )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            raise ValidationError("לא נמצא חשבון עם כתובת דוא\"ל זו.")
        
        user = User.objects.get(email=email)
        if hasattr(user, 'is_student') and user.is_student and not email.endswith('@ac.sce.ac.il'):
            raise ValidationError("חשבונות סטודנטים חייבים להשתמש בדוא\"ל @ac.sce.ac.il")
        if hasattr(user, 'is_lecturer') and user.is_lecturer and not email.endswith('@sce.ac.il'):
            raise ValidationError("חשבונות מרצים חייבים להשתמש בדוא\"ל @sce.ac.il")
        
        return email

    def clean_code(self):
        if self.stage != 'reset':
            return None
            
        code = self.cleaned_data.get('code')
        if not code or len(code) != 6:
            raise ValidationError("פורמט קוד אימות לא תקין")
        
        return code

    def clean(self):
        cleaned_data = super().clean()
        
        if self.stage in ['change', 'reset']:
            new_password1 = cleaned_data.get('new_password1')
            new_password2 = cleaned_data.get('new_password2')
            
            if new_password1 and new_password2 and new_password1 != new_password2:
                raise ValidationError("שני שדות הסיסמה לא תואמים.")
            
            if self.stage == 'change':
                old_password = cleaned_data.get('old_password')
                if old_password and self.user and not self.user.check_password(old_password):
                    raise ValidationError("הסיסמה הנוכחית שהוזנה שגויה.")
        
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