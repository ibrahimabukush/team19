# tests/test_models.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from blog.models import AcademicRequest, ScheduleRequest, PersonalRequest
from users.models import Subject, LecturerProfile
from .test_utils import TestDataMixin

User = get_user_model()

class UserModelTest(TestCase, TestDataMixin):
    """Test User model functionality"""
    
    def setUp(self):
        self.create_test_users()
    
    def test_user_creation(self):
        """Test that users are created correctly"""
        self.assertTrue(self.student.is_student)
        self.assertFalse(self.student.is_lecturer)
        self.assertFalse(self.student.is_secretary)
        
        self.assertTrue(self.lecturer.is_lecturer)
        self.assertFalse(self.lecturer.is_student)
        
        self.assertTrue(self.secretary.is_secretary)
        self.assertFalse(self.secretary.is_student)
    
    def test_user_str_method(self):
        """Test user string representation"""
        self.assertEqual(str(self.student), 'test_student')
    
    def test_user_get_full_name(self):
        """Test get_full_name method"""
        self.assertEqual(self.student.get_full_name(), 'Test Student')
    
    def test_user_department_field(self):
        """Test department field"""
        self.assertEqual(self.student.department, 'מדעי המחשב')
        self.assertEqual(self.lecturer.department, 'מדעי המחשב')

class SubjectModelTest(TestCase, TestDataMixin):
    """Test Subject model functionality"""
    
    def setUp(self):
        self.create_test_users()
        self.create_test_subjects()
    
    def test_subject_creation(self):
        """Test subject creation"""
        self.assertEqual(self.subject1.name, 'מבני נתונים')
        self.assertEqual(self.subject1.department, 'מדעי המחשב')
        self.assertEqual(self.subject1.lecturer, self.lecturer)
    
    def test_subject_str_method(self):
        """Test subject string representation"""
        expected = f"מבני נתונים - {self.lecturer.get_full_name()}"
        self.assertEqual(str(self.subject1), expected)
    
    def test_subject_department_filtering(self):
        """Test filtering subjects by department"""
        subjects = Subject.objects.filter(department='מדעי המחשב')
        self.assertEqual(subjects.count(), 2)

class AcademicRequestModelTest(TestCase, TestDataMixin):
    """Test AcademicRequest model functionality"""
    
    def setUp(self):
        self.create_test_users()
        self.create_test_requests()
    
    def test_academic_request_creation(self):
        """Test academic request creation"""
        self.assertEqual(self.academic_request_lecturer.student, self.student)
        self.assertEqual(self.academic_request_lecturer.request_type, 'academic_appeal')
        self.assertEqual(self.academic_request_lecturer.status, 'pending')
    
    def test_academic_request_str_method(self):
        """Test academic request string representation"""
        expected = f"Academic Request #{self.academic_request_lecturer.id} - {self.student.username}"
        self.assertEqual(str(self.academic_request_lecturer), expected)
    
    def test_request_type_choices(self):
        """Test that request type choices are valid"""
        valid_types = ['enrollment_confirmation', 'academic_appeal', 'exam_review']
        self.assertIn(self.academic_request_lecturer.request_type, valid_types)
        self.assertIn(self.academic_request_secretary.request_type, valid_types)
    
    def test_status_choices(self):
        """Test that status choices are valid"""
        valid_statuses = ['pending', 'in_progress', 'need_update', 'approved', 'rejected']
        self.assertIn(self.academic_request_lecturer.status, valid_statuses)
    
    def test_lecturer_note_field(self):
        """Test lecturer note field"""
        self.academic_request_lecturer.lecturer_note = "Test note from lecturer"
        self.academic_request_lecturer.save()
        
        retrieved = AcademicRequest.objects.get(id=self.academic_request_lecturer.id)
        self.assertEqual(retrieved.lecturer_note, "Test note from lecturer")
    
    def test_update_deadline_field(self):
        """Test update deadline field"""
        future_date = timezone.now().date() + timedelta(days=7)
        self.academic_request_lecturer.update_deadline = future_date
        self.academic_request_lecturer.save()
        
        retrieved = AcademicRequest.objects.get(id=self.academic_request_lecturer.id)
        self.assertEqual(retrieved.update_deadline, future_date)

class ScheduleRequestModelTest(TestCase, TestDataMixin):
    """Test ScheduleRequest model functionality"""
    
    def setUp(self):
        self.create_test_users()
        self.create_test_requests()
    
    def test_schedule_request_creation(self):
        """Test schedule request creation"""
        self.assertEqual(self.schedule_request.student, self.student)
        self.assertEqual(self.schedule_request.request_type, 'schedule_change')
        self.assertEqual(self.schedule_request.status, 'pending')
    
    def test_schedule_request_str_method(self):
        """Test schedule request string representation"""
        expected = f"Schedule Request #{self.schedule_request.id} - {self.student.username}"
        self.assertEqual(str(self.schedule_request), expected)
    
    def test_schedule_request_types(self):
        """Test valid schedule request types"""
        valid_types = ['schedule_change', 'extension_request', 'special_exam_date', 'approved_absence']
        self.assertIn(self.schedule_request.request_type, valid_types)

class PersonalRequestModelTest(TestCase, TestDataMixin):
    """Test PersonalRequest model functionality"""
    
    def setUp(self):
        self.create_test_users()
        self.create_test_requests()
    
    def test_personal_request_creation(self):
        """Test personal request creation"""
        self.assertEqual(self.personal_request_lecturer.student, self.student)
        self.assertEqual(self.personal_request_lecturer.request_type, 'recommendation_letter')
        self.assertEqual(self.personal_request_lecturer.status, 'pending')
    
    def test_personal_request_str_method(self):
        """Test personal request string representation"""
        expected = f"Personal Request #{self.personal_request_lecturer.id} - {self.student.username}"
        self.assertEqual(str(self.personal_request_lecturer), expected)
    
    def test_personal_request_types(self):
        """Test valid personal request types"""
        valid_types = [
            'recommendation_letter', 'personal_details_update',
            'certificates_confirmations', 'scholarships_financial_aid',
            'academic_status_change', 'general_manager_inquiry'
        ]
        self.assertIn(self.personal_request_lecturer.request_type, valid_types)
        self.assertIn(self.personal_request_secretary.request_type, valid_types)

class LecturerProfileModelTest(TestCase, TestDataMixin):
    """Test LecturerProfile model functionality"""
    
    def setUp(self):
        self.create_test_users()
    
    def test_lecturer_profile_creation(self):
        """Test lecturer profile creation"""
        self.assertEqual(self.lecturer_profile.user, self.lecturer)
        self.assertEqual(self.lecturer_profile.subject, 'מבני נתונים, אלגוריתמים')
    
    def test_lecturer_profile_str_method(self):
        """Test lecturer profile string representation"""
        expected = f"Lecturer Profile - {self.lecturer.get_full_name()}"
        self.assertEqual(str(self.lecturer_profile), expected)

class ModelRelationshipsTest(TestCase, TestDataMixin):
    """Test model relationships and constraints"""
    
    def setUp(self):
        self.create_test_users()
        self.create_test_subjects()
        self.create_test_requests()
    
    def test_student_requests_relationship(self):
        """Test that student can have multiple requests"""
        student_academic_requests = AcademicRequest.objects.filter(student=self.student)
        student_schedule_requests = ScheduleRequest.objects.filter(student=self.student)
        student_personal_requests = PersonalRequest.objects.filter(student=self.student)
        
        self.assertGreaterEqual(student_academic_requests.count(), 1)
        self.assertGreaterEqual(student_schedule_requests.count(), 1)
        self.assertGreaterEqual(student_personal_requests.count(), 1)
    
    def test_lecturer_subjects_relationship(self):
        """Test lecturer can have multiple subjects"""
        lecturer_subjects = Subject.objects.filter(lecturer=self.lecturer)
        self.assertGreaterEqual(lecturer_subjects.count(), 1)
    
    def test_department_consistency(self):
        """Test that users and subjects have consistent departments"""
        # All test data should be in the same department
        self.assertEqual(self.student.department, self.lecturer.department)
        self.assertEqual(self.subject1.department, self.lecturer.department)
        self.assertEqual(self.subject2.department, self.lecturer.department)

class ModelValidationTest(TestCase, TestDataMixin):
    """Test model validation rules"""
    
    def setUp(self):
        self.create_test_users()
    
    def test_email_validation(self):
        """Test email field validation"""
        # Test invalid email
        with self.assertRaises(ValidationError):
            user = User(
                username='test_invalid',
                email='invalid-email',
                department='מדעי המחשב'
            )
            user.full_clean()
    
    def test_required_fields(self):
        """Test required field validation"""
        # Test missing username
        with self.assertRaises(ValidationError):
            user = User(
                email='test@test.com',
                department='מדעי המחשב'
            )
            user.full_clean()
    
    def test_department_field(self):
        """Test department field constraints"""
        # Department should be required for most user types
        user = User.objects.create_user(
            username='test_no_dept',
            email='test@test.com',
            password='testpass123'
        )
        # This should be allowed but department should be empty
        self.assertEqual(user.department, '')