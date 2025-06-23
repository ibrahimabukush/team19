# tests/test_views.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.contrib.messages import get_messages
from unittest.mock import patch, MagicMock
import json
from blog.models import AcademicRequest, ScheduleRequest, PersonalRequest
from users.models import Subject
from .test_utils import TestDataMixin

User = get_user_model()

class BaseViewTest(TestCase, TestDataMixin):
    """Base class for view tests"""
    
    def setUp(self):
        self.client = Client()
        self.create_test_users()
        self.create_test_subjects()
        self.create_test_requests()

class HomeViewTest(BaseViewTest):
    """Test home page view"""
    
    def test_home_view_get(self):
        """Test GET request to home page"""
        response = self.client.get(reverse('blog-home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ISEND')  # Assuming this appears in your home template
    
    def test_home_view_redirects_secretary(self):
        """Test that secretary is redirected to dashboard"""
        self.client.login(username='test_secretary', password='testpass123')
        response = self.client.get(reverse('blog-home'))
        self.assertRedirects(response, reverse('secretary_dashboard'))

class AcademicRequestViewTest(BaseViewTest):
    """Test academic request views"""
    
    def test_academic_request_view_requires_login(self):
        """Test that academic request view requires login"""
        response = self.client.get(reverse('academic_request'))
        self.assertRedirects(response, '/login/?next=' + reverse('academic_request'))
    
    def test_academic_request_view_logged_in(self):
        """Test academic request view when logged in"""
        self.client.login(username='test_student', password='testpass123')
        response = self.client.get(reverse('academic_request'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('subjects', response.context)
    
    def test_academic_request_subjects_filtered_by_department(self):
        """Test that subjects are filtered by user's department"""
        self.client.login(username='test_student', password='testpass123')
        response = self.client.get(reverse('academic_request'))
        
        subjects = response.context['subjects']
        for subject in subjects:
            self.assertEqual(subject['department'], self.student.department)
    
    def test_submit_academic_request_valid(self):
        """Test submitting a valid academic request"""
        self.client.login(username='test_student', password='testpass123')
        
        data = {
            'request_type': 'ערעורים אקדמיים',
            'subject': 'מבני נתונים',
            'request_text': 'I would like to appeal my grade'
        }
        
        response = self.client.post(reverse('submit_request'), data)
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'success')
        
        # Check that request was created
        self.assertTrue(
            AcademicRequest.objects.filter(
                student=self.student,
                request_type='academic_appeal'
            ).exists()
        )
    
    def test_submit_academic_request_missing_subject(self):
        """Test submitting academic request without required subject"""
        self.client.login(username='test_student', password='testpass123')
        
        data = {
            'request_type': 'ערעורים אקדמיים',
            'request_text': 'I would like to appeal my grade'
            # Missing subject
        }
        
        response = self.client.post(reverse('submit_request'), data)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'error')
        self.assertIn('בחר קורס', response_data['message'])
    
    def test_submit_academic_request_missing_description(self):
        """Test submitting academic request without description"""
        self.client.login(username='test_student', password='testpass123')
        
        data = {
            'request_type': 'ערעורים אקדמיים',
            'subject': 'מבני נתונים'
            # Missing request_text
        }
        
        response = self.client.post(reverse('submit_request'), data)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'error')
        self.assertIn('תאר את בקשתך', response_data['message'])

class LecturerDashboardViewTest(BaseViewTest):
    """Test lecturer dashboard view"""
    
    def test_lecturer_dashboard_requires_lecturer_role(self):
        """Test that only lecturers can access lecturer dashboard"""
        # Test with student
        self.client.login(username='test_student', password='testpass123')
        response = self.client.get(reverse('lecturer_dashboard'))
        self.assertRedirects(response, reverse('blog-home'))
        
        # Test with secretary
        self.client.login(username='test_secretary', password='testpass123')
        response = self.client.get(reverse('lecturer_dashboard'))
        self.assertRedirects(response, reverse('blog-home'))
    
    def test_lecturer_dashboard_success(self):
        """Test lecturer dashboard access with proper role"""
        self.client.login(username='test_lecturer', password='testpass123')
        response = self.client.get(reverse('lecturer_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('all_requests', response.context)
        self.assertIn('stats', response.context)
    
    def test_lecturer_dashboard_shows_only_lecturer_requests(self):
        """Test that lecturer dashboard shows only lecturer-handled requests"""
        self.client.login(username='test_lecturer', password='testpass123')
        response = self.client.get(reverse('lecturer_dashboard'))
        
        # Should show academic appeals and recommendation letters
        requests = response.context['all_requests']
        for request in requests:
            if hasattr(request, 'request_type'):
                self.assertIn(request.request_type, [
                    'academic_appeal', 'exam_review', 'recommendation_letter'
                ])

class SecretaryDashboardViewTest(BaseViewTest):
    """Test secretary dashboard view"""
    
    def test_secretary_dashboard_requires_secretary_role(self):
        """Test that only secretaries can access secretary dashboard"""
        # Test with student
        self.client.login(username='test_student', password='testpass123')
        response = self.client.get(reverse('secretary_dashboard'))
        self.assertRedirects(response, reverse('blog-home'))
        
        # Test with lecturer
        self.client.login(username='test_lecturer', password='testpass123')
        response = self.client.get(reverse('secretary_dashboard'))
        self.assertRedirects(response, reverse('blog-home'))
    
    def test_secretary_dashboard_success(self):
        """Test secretary dashboard access with proper role"""
        self.client.login(username='test_secretary', password='testpass123')
        response = self.client.get(reverse('secretary_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('all_requests', response.context)
        self.assertIn('stats', response.context)

class UpdateRequestStatusViewTest(BaseViewTest):
    """Test request status update views"""
    
    def test_update_academic_request_status_lecturer(self):
        """Test lecturer updating academic request status"""
        self.client.login(username='test_lecturer', password='testpass123')
        
        # Test updating lecturer-handled academic request
        data = {
            'status': 'approved',
            'lecturer_note': 'Request approved',
            'request_type': 'academic'
        }
        
        url = reverse('lecturer_update_request_status', 
                     args=[self.academic_request_lecturer.id])
        response = self.client.post(url, data, 
                                  HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Check that status was updated
        self.academic_request_lecturer.refresh_from_db()
        self.assertEqual(self.academic_request_lecturer.status, 'approved')
        self.assertEqual(self.academic_request_lecturer.lecturer_note, 'Request approved')
    
    def test_update_secretary_only_request_by_lecturer_fails(self):
        """Test that lecturer cannot update secretary-only requests"""
        self.client.login(username='test_lecturer', password='testpass123')
        
        data = {
            'status': 'approved',
            'lecturer_note': 'Should not work',
            'request_type': 'academic'
        }
        
        # Try to update enrollment confirmation (secretary-only)
        url = reverse('lecturer_update_request_status', 
                     args=[self.academic_request_secretary.id])
        response = self.client.post(url, data, 
                                  HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('secretary', response_data['message'].lower())
    
    def test_update_request_status_secretary(self):
        """Test secretary updating request status"""
        self.client.login(username='test_secretary', password='testpass123')
        
        data = {
            'status': 'approved',
            'secretary_note': 'Request approved by secretary',
            'request_type': 'schedule'
        }
        
        url = reverse('update_request_status', args=[self.schedule_request.id])
        response = self.client.post(url, data, 
                                  HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Check that status was updated
        self.schedule_request.refresh_from_db()
        self.assertEqual(self.schedule_request.status, 'approved')

class TrackingViewTest(BaseViewTest):
    """Test tracking view"""
    
    def test_tracking_view_requires_login(self):
        """Test that tracking view requires login"""
        response = self.client.get(reverse('tracking'))
        self.assertRedirects(response, '/login/?next=' + reverse('tracking'))
    
    def test_tracking_view_shows_user_requests(self):
        """Test that tracking view shows only current user's requests"""
        self.client.login(username='test_student', password='testpass123')
        response = self.client.get(reverse('tracking'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('requests', response.context)
        
        # All requests should belong to the logged-in student
        requests = response.context['requests']
        for request in requests:
            self.assertEqual(request.student, self.student)

class GetLecturerViewTest(BaseViewTest):
    """Test get lecturer API view"""
    
    def test_get_lecturer_valid_subject(self):
        """Test getting lecturer for valid subject"""
        self.client.login(username='test_student', password='testpass123')
        
        response = self.client.get(reverse('get_lecturer'), {
            'subject': 'מבני נתונים'
        })
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertIsNotNone(response_data['lecturer_name'])
        self.assertEqual(response_data['lecturer_id'], self.lecturer.id)
    
    def test_get_lecturer_invalid_subject(self):
        """Test getting lecturer for invalid subject"""
        self.client.login(username='test_student', password='testpass123')
        
        response = self.client.get(reverse('get_lecturer'), {
            'subject': 'Non-existent Subject'
        })
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertIsNone(response_data['lecturer_name'])
        self.assertIsNone(response_data['lecturer_id'])

class PersonalRequestViewTest(BaseViewTest):
    """Test personal request views"""
    
    def test_submit_personal_request_valid(self):
        """Test submitting valid personal request"""
        self.client.login(username='test_student', password='testpass123')
        
        data = {
            'request_type': 'עדכון פרטים אישיים',
            'request_text': 'I need to update my contact information'
        }
        
        response = self.client.post(reverse('submit_personal_requests'), data)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'success')
        
        # Check that request was created
        self.assertTrue(
            PersonalRequest.objects.filter(
                student=self.student,
                request_type='personal_details_update'
            ).exists()
        )
    
    def test_submit_recommendation_letter_request_with_lecturer(self):
        """Test submitting recommendation letter request with lecturer selection"""
        self.client.login(username='test_student', password='testpass123')
        
        data = {
            'request_type': 'בקשה למכתבי המלצה',
            'request_text': 'I need a recommendation letter',
            'selected_lecturer': str(self.lecturer.id)
        }
        
        response = self.client.post(reverse('submit_personal_requests'), data)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'success')

class ScheduleRequestViewTest(BaseViewTest):
    """Test schedule request views"""
    
    def test_submit_schedule_request_valid(self):
        """Test submitting valid schedule request"""
        self.client.login(username='test_student', password='testpass123')
        
        data = {
            'request_type': 'שינוי מערכת שעות',
            'request_text': 'I need to change my class schedule'
        }
        
        response = self.client.post(reverse('submit_schedule_request'), data)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'success')
        
        # Check that request was created
        self.assertTrue(
            ScheduleRequest.objects.filter(
                student=self.student,
                request_type='schedule_change'
            ).exists()
        )