# tests/test_utils.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from blog.models import AcademicRequest, ScheduleRequest, PersonalRequest
from users.models import Subject, LecturerProfile
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

class TestDataMixin:
    """Mixin providing common test data creation methods"""
    
    @classmethod
    def create_test_users(cls):
        """Create test users for different roles"""
        # Create student
        cls.student = User.objects.create_user(
            username='test_student',
            email='student@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Student',
            department='מדעי המחשב',
            is_student=True
        )
        
        # Create lecturer
        cls.lecturer = User.objects.create_user(
            username='test_lecturer',
            email='lecturer@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Lecturer',
            department='מדעי המחשב',
            is_lecturer=True
        )
        
        # Create secretary
        cls.secretary = User.objects.create_user(
            username='test_secretary',
            email='secretary@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Secretary',
            department='מדעי המחשב',
            is_secretary=True
        )
        
        # Create lecturer profile
        cls.lecturer_profile = LecturerProfile.objects.create(
            user=cls.lecturer,
            subject='מבני נתונים, אלגוריתמים'
        )
    
    @classmethod
    def create_test_subjects(cls):
        """Create test subjects"""
        cls.subject1 = Subject.objects.create(
            name='מבני נתונים',
            department='מדעי המחשב',
            lecturer=cls.lecturer
        )
        
        cls.subject2 = Subject.objects.create(
            name='אלגוריתמים',
            department='מדעי המחשב',
            lecturer=cls.lecturer
        )
    
    @classmethod
    def create_test_requests(cls):
        """Create test requests"""
        # Academic request (lecturer-handled)
        cls.academic_request_lecturer = AcademicRequest.objects.create(
            student=cls.student,
            subject='מבני נתונים',
            request_type='academic_appeal',
            request_text='I would like to appeal my grade',
            status='pending'
        )
        
        # Academic request (secretary-handled)
        cls.academic_request_secretary = AcademicRequest.objects.create(
            student=cls.student,
            subject='',
            request_type='enrollment_confirmation',
            request_text='I need enrollment confirmation',
            status='pending'
        )
        
        # Schedule request (always secretary-handled)
        cls.schedule_request = ScheduleRequest.objects.create(
            student=cls.student,
            request_type='schedule_change',
            request_text='I need to change my schedule',
            status='pending'
        )
        
        # Personal request (lecturer-handled)
        cls.personal_request_lecturer = PersonalRequest.objects.create(
            student=cls.student,
            request_type='recommendation_letter',
            request_text='I need a recommendation letter',
            status='pending'
        )
        
        # Personal request (secretary-handled)
        cls.personal_request_secretary = PersonalRequest.objects.create(
            student=cls.student,
            request_type='personal_details_update',
            request_text='I need to update my personal details',
            status='pending'
        )
    
    @classmethod
    def create_test_file(cls):
        """Create a test file for uploads"""
        return SimpleUploadedFile(
            "test_file.pdf",
            b"file_content",
            content_type="application/pdf"
        )