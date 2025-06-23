# tests/test_integration.py
from django.test import TestCase, Client, TransactionTestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db import transaction
from django.test.utils import override_settings
from django.core import mail
from django.contrib.messages import get_messages
import json
import time
from blog.models import AcademicRequest, ScheduleRequest, PersonalRequest
from users.models import Subject, LecturerProfile
from .test_utils import TestDataMixin

User = get_user_model()

class RequestWorkflowIntegrationTest(TestCase, TestDataMixin):
    """Integration tests for complete request workflows"""
    
    def setUp(self):
        self.client = Client()
        self.create_test_users()
        self.create_test_subjects()
    
    def test_complete_academic_request_workflow_lecturer_handled(self):
        """Test complete workflow for lecturer-handled academic request"""
        # Step 1: Student logs in and submits academic appeal
        self.client.login(username='test_student', password='testpass123')
        
        # Student submits request
        submit_data = {
            'request_type': 'ערעורים אקדמיים',
            'subject': 'מבני נתונים',
            'request_text': 'I would like to appeal my grade for the final exam'
        }
        
        response = self.client.post(reverse('submit_request'), submit_data)
        self.assertEqual(response.status_code, 200)
        
        # Verify request was created
        request_obj = AcademicRequest.objects.get(
            student=self.student,
            request_type='academic_appeal'
        )
        self.assertEqual(request_obj.status, 'pending')
        
        # Step 2: Student checks tracking
        response = self.client.get(reverse('tracking'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ערעורים אקדמיים')
        
        # Step 3: Lecturer logs in and views dashboard
        self.client.login(username='test_lecturer', password='testpass123')
        response = self.client.get(reverse('lecturer_dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Verify request appears in lecturer dashboard
        self.assertContains(response, 'appeal my grade')
        
        # Step 4: Lecturer updates request status to in_progress
        update_data = {
            'status': 'in_progress',
            'lecturer_note': 'Review started, will examine exam papers',
            'request_type': 'academic'
        }
        
        response = self.client.post(
            reverse('lecturer_update_request_status', args=[request_obj.id]),
            update_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Verify status update
        request_obj.refresh_from_db()
        self.assertEqual(request_obj.status, 'in_progress')
        self.assertEqual(request_obj.lecturer_note, 'Review started, will examine exam papers')
        
        # Step 5: Student checks tracking again
        self.client.login(username='test_student', password='testpass123')
        response = self.client.get(reverse('tracking'))
        self.assertContains(response, 'בטיפול')
        self.assertContains(response, 'Review started')
        
        # Step 6: Lecturer approves the request
        self.client.login(username='test_lecturer', password='testpass123')
        approve_data = {
            'status': 'approved',
            'lecturer_note': 'Grade appeal approved. Grade changed from B+ to A-',
            'request_type': 'academic'
        }
        
        response = self.client.post(
            reverse('lecturer_update_request_status', args=[request_obj.id]),
            approve_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify final status
        request_obj.refresh_from_db()
        self.assertEqual(request_obj.status, 'approved')
        self.assertIn('Grade changed', request_obj.lecturer_note)
        
        # Step 7: Student sees final result
        self.client.login(username='test_student', password='testpass123')
        response = self.client.get(reverse('tracking'))
        self.assertContains(response, 'אושר')
        self.assertContains(response, 'Grade changed')
    
    def test_complete_schedule_request_workflow_secretary_handled(self):
        """Test complete workflow for secretary-handled schedule request"""
        # Step 1: Student submits schedule request
        self.client.login(username='test_student', password='testpass123')
        
        submit_data = {
            'request_type': 'שינוי מערכת שעות',
            'request_text': 'I have a conflict between two mandatory courses'
        }
        
        response = self.client.post(reverse('submit_schedule_request'), submit_data)
        self.assertEqual(response.status_code, 200)
        
        # Verify request was created
        request_obj = ScheduleRequest.objects.get(
            student=self.student,
            request_type='schedule_change'
        )
        
        # Step 2: Secretary logs in and handles request
        self.client.login(username='test_secretary', password='testpass123')
        response = self.client.get(reverse('secretary_dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Step 3: Secretary updates status
        update_data = {
            'status': 'approved',
            'secretary_note': 'Schedule conflict resolved. New slot assigned.',
            'request_type': 'schedule'
        }
        
        response = self.client.post(
            reverse('update_request_status', args=[request_obj.id]),
            update_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify status update
        request_obj.refresh_from_db()
        self.assertEqual(request_obj.status, 'approved')
    
    def test_request_requiring_update_workflow(self):
        """Test workflow for request that requires student update"""
        # Create initial request
        self.client.login(username='test_student', password='testpass123')
        
        submit_data = {
            'request_type': 'בקשה למכתבי המלצה',
            'request_text': 'I need a recommendation letter',
            'selected_lecturer': str(self.lecturer.id)
        }
        
        response = self.client.post(reverse('submit_personal_requests'), submit_data)
        self.assertEqual(response.status_code, 200)
        
        request_obj = PersonalRequest.objects.get(
            student=self.student,
            request_type='recommendation_letter'
        )
        
        # Lecturer requests more information
        self.client.login(username='test_lecturer', password='testpass123')
        
        from datetime import datetime, timedelta
        future_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        
        update_data = {
            'status': 'need_update',
            'lecturer_note': 'Please provide your CV and transcript',
            'update_deadline': future_date,
            'request_type': 'personal'
        }
        
        response = self.client.post(
            reverse('lecturer_update_request_status', args=[request_obj.id]),
            update_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify update
        request_obj.refresh_from_db()
        self.assertEqual(request_obj.status, 'need_update')
        self.assertIsNotNone(request_obj.update_deadline)
        
        # Student checks tracking and sees update requirement
        self.client.login(username='test_student', password='testpass123')
        response = self.client.get(reverse('tracking'))
        self.assertContains(response, 'נדרש עדכון')
        self.assertContains(response, 'CV and transcript')

class RoleBasedAccessIntegrationTest(TestCase, TestDataMixin):
    """Integration tests for role-based access control"""
    
    def setUp(self):
        self.client = Client()
        self.create_test_users()
        self.create_test_requests()
    
    def test_lecturer_cannot_access_secretary_only_requests(self):
        """Test that lecturer cannot access secretary-only requests"""
        self.client.login(username='test_lecturer', password='testpass123')
        
        # Try to update enrollment confirmation (secretary-only)
        update_data = {
            'status': 'approved',
            'lecturer_note': 'Should not work',
            'request_type': 'academic'
        }
        
        response = self.client.post(
            reverse('lecturer_update_request_status', 
                   args=[self.academic_request_secretary.id]),
            update_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        
        # Verify status was not changed
        self.academic_request_secretary.refresh_from_db()
        self.assertEqual(self.academic_request_secretary.status, 'pending')
    
    def test_secretary_cannot_access_lecturer_dashboard(self):
        """Test that secretary cannot access lecturer dashboard"""
        self.client.login(username='test_secretary', password='testpass123')
        response = self.client.get(reverse('lecturer_dashboard'))
        self.assertRedirects(response, reverse('blog-home'))
    
    def test_student_cannot_access_admin_functions(self):
        """Test that student cannot access admin functions"""
        self.client.login(username='test_student', password='testpass123')
        
        # Try to access secretary dashboard
        response = self.client.get(reverse('secretary_dashboard'))
        self.assertRedirects(response, reverse('blog-home'))
        
        # Try to access lecturer dashboard
        response = self.client.get(reverse('lecturer_dashboard'))
        self.assertRedirects(response, reverse('blog-home'))
    
    def test_cross_department_access_restriction(self):
        """Test that users cannot access requests from other departments"""
        # Create user from different department
        other_dept_student = User.objects.create_user(
            username='other_student',
            email='other@test.com',
            password='testpass123',
            department='הנדסת תוכנה',
            is_student=True
        )
        
        other_dept_lecturer = User.objects.create_user(
            username='other_lecturer',
            email='other_lecturer@test.com',
            password='testpass123',
            department='הנדסת תוכנה',
            is_lecturer=True
        )
        
        # Create request from other department
        other_request = AcademicRequest.objects.create(
            student=other_dept_student,
            subject='Other Subject',
            request_type='academic_appeal',
            request_text='Other department request',
            status='pending'
        )
        
        # Try to access with lecturer from different department
        self.client.login(username='test_lecturer', password='testpass123')
        
        update_data = {
            'status': 'approved',
            'lecturer_note': 'Should not work',
            'request_type': 'academic'
        }
        
        response = self.client.post(
            reverse('lecturer_update_request_status', args=[other_request.id]),
            update_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])

class DataConsistencyIntegrationTest(TransactionTestCase):
    """Integration tests for data consistency across the application"""
    
    def setUp(self):
        self.client = Client()
        # Create test data
        self.student = User.objects.create_user(
            username='test_student',
            email='student@test.com',
            password='testpass123',
            department='מדעי המחשב',
            is_student=True
        )
        
        self.lecturer = User.objects.create_user(
            username='test_lecturer',
            email='lecturer@test.com',
            password='testpass123',
            department='מדעי המחשב',
            is_lecturer=True
        )
    
    def test_concurrent_request_updates(self):
        """Test handling of concurrent request updates"""
        # Create request
        request_obj = AcademicRequest.objects.create(
            student=self.student,
            subject='Test Subject',
            request_type='academic_appeal',
            request_text='Test request',
            status='pending'
        )
        
        self.client.login(username='test_lecturer', password='testpass123')
        
        # Simulate concurrent updates
        update_data1 = {
            'status': 'in_progress',
            'lecturer_note': 'First update',
            'request_type': 'academic'
        }
        
        update_data2 = {
            'status': 'approved',
            'lecturer_note': 'Second update',
            'request_type': 'academic'
        }
        
        # Both updates should work, but second one should be final
        response1 = self.client.post(
            reverse('lecturer_update_request_status', args=[request_obj.id]),
            update_data1,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        response2 = self.client.post(
            reverse('lecturer_update_request_status', args=[request_obj.id]),
            update_data2,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        
        # Final status should be from second update
        request_obj.refresh_from_db()
        self.assertEqual(request_obj.status, 'approved')
        self.assertEqual(request_obj.lecturer_note, 'Second update')

class PerformanceIntegrationTest(TestCase, TestDataMixin):
    """Integration tests for performance aspects"""
    
    def setUp(self):
        self.client = Client()
        self.create_test_users()
        self.create_test_subjects()
        
        # Create multiple requests for performance testing
        for i in range(50):
            AcademicRequest.objects.create(
                student=self.student,
                subject='מבני נתונים',
                request_type='academic_appeal',
                request_text=f'Test request {i}',
                status='pending'
            )
    
    def test_dashboard_performance_with_many_requests(self):
        """Test dashboard performance with many requests"""
        self.client.login(username='test_lecturer', password='testpass123')
        
        start_time = time.time()
        response = self.client.get(reverse('lecturer_dashboard'))
        end_time = time.time()
        
        self.assertEqual(response.status_code, 200)
        # Dashboard should load within reasonable time (5 seconds)
        self.assertLess(end_time - start_time, 5.0)
    
    def test_tracking_performance_with_many_requests(self):
        """Test tracking page performance with many requests"""
        self.client.login(username='test_student', password='testpass123')
        
        start_time = time.time()
        response = self.client.get(reverse('tracking'))
        end_time = time.time()
        
        self.assertEqual(response.status_code, 200)
        # Tracking should load within reasonable time (3 seconds)
        self.assertLess(end_time - start_time, 3.0)

@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class EmailIntegrationTest(TestCase, TestDataMixin):
    """Integration tests for email functionality"""
    
    def setUp(self):
        self.client = Client()
        self.create_test_users()
    
    def test_registration_email_sent(self):
        """Test that welcome email is sent on registration"""
        registration_data = {
            'username': 'new_student',
            'email': 'new_student@test.com',
            'password1': 'complexpass123',
            'password2': 'complexpass123',
            'department': 'מדעי המחשב',
            'year': '1',
            'user_type': 'student'
        }
        
        response = self.client.post(reverse('register'), registration_data)
        
        # Check that welcome email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Welcome to ISEND', mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to, ['new_student@test.com'])
    
    def test_login_notification_email(self):
        """Test that login notification email is sent"""
        self.client.login(username='test_student', password='testpass123')
        
        # Check that login email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('New Login Detected', mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to, [self.student.email])