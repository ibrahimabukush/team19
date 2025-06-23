# tests/test_api.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.http import JsonResponse
import json
from unittest.mock import patch, MagicMock
from blog.models import AcademicRequest, ScheduleRequest, PersonalRequest
from users.models import Subject
from .test_utils import TestDataMixin

User = get_user_model()

class APIResponseTest(TestCase, TestDataMixin):
    """Test API responses and JSON formatting"""
    
    def setUp(self):
        self.client = Client()
        self.create_test_users()
        self.create_test_subjects()
        self.create_test_requests()
    
    def test_get_lecturer_api_response_format(self):
        """Test get lecturer API response format"""
        self.client.login(username='test_student', password='testpass123')
        
        response = self.client.get(reverse('get_lecturer'), {
            'subject': 'מבני נתונים'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = json.loads(response.content)
        self.assertIn('lecturer_name', data)
        self.assertIn('lecturer_id', data)
        self.assertIsInstance(data['lecturer_name'], str)
        self.assertIsInstance(data['lecturer_id'], int)
    
    def test_get_lecturer_api_no_subject(self):
        """Test get lecturer API with no subject parameter"""
        self.client.login(username='test_student', password='testpass123')
        
        response = self.client.get(reverse('get_lecturer'))
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIsNone(data['lecturer_name'])
        self.assertIsNone(data['lecturer_id'])
    
    def test_get_lecturer_api_invalid_subject(self):
        """Test get lecturer API with invalid subject"""
        self.client.login(username='test_student', password='testpass123')
        
        response = self.client.get(reverse('get_lecturer'), {
            'subject': 'Non-existent Subject'
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIsNone(data['lecturer_name'])
        self.assertIsNone(data['lecturer_id'])
        self.assertIn('error', data)
    
    def test_submit_request_api_success_response(self):
        """Test submit request API success response format"""
        self.client.login(username='test_student', password='testpass123')
        
        data = {
            'request_type': 'ערעורים אקדמיים',
            'subject': 'מבני נתונים',
            'request_text': 'Test request'
        }
        
        response = self.client.post(reverse('submit_request'), data)
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'success')
        self.assertIn('message', response_data)
    
    def test_submit_request_api_error_response(self):
        """Test submit request API error response format"""
        self.client.login(username='test_student', password='testpass123')
        
        data = {
            'request_type': 'ערעורים אקדמיים',
            # Missing required fields
        }
        
        response = self.client.post(reverse('submit_request'), data)
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'error')
        self.assertIn('message', response_data)
    
    def test_update_request_status_api_success(self):
        """Test update request status API success response"""
        self.client.login(username='test_lecturer', password='testpass123')
        
        data = {
            'status': 'approved',
            'lecturer_note': 'Test note',
            'request_type': 'academic'
        }
        
        response = self.client.post(
            reverse('lecturer_update_request_status', 
                   args=[self.academic_request_lecturer.id]),
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertIn('message', response_data)
        self.assertIn('old_status', response_data)
        self.assertIn('new_status', response_data)
    
    def test_update_request_status_api_error(self):
        """Test update request status API error response"""
        self.client.login(username='test_lecturer', password='testpass123')
        
        data = {
            'status': 'invalid_status',
            'lecturer_note': 'Test note',
            'request_type': 'academic'
        }
        
        response = self.client.post(
            reverse('lecturer_update_request_status', 
                   args=[self.academic_request_lecturer.id]),
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('message', response_data)

class APIAuthenticationTest(TestCase, TestDataMixin):
    """Test API authentication and authorization"""
    
    def setUp(self):
        self.client = Client()
        self.create_test_users()
        self.create_test_requests()
    
    def test_update_request_status_requires_login(self):
        """Test that update request status requires login"""
        data = {
            'status': 'approved',
            'lecturer_note': 'Test note'
        }
        
        response = self.client.post(
            reverse('lecturer_update_request_status', 
                   args=[self.academic_request_lecturer.id]),
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        # Should redirect to login or return 401/403
        self.assertIn(response.status_code, [302, 401, 403])
    
    def test_update_request_status_requires_lecturer_role(self):
        """Test that update request status requires lecturer role"""
        self.client.login(username='test_student', password='testpass123')
        
        data = {
            'status': 'approved',
            'lecturer_note': 'Test note'
        }
        
        response = self.client.post(
            reverse('lecturer_update_request_status', 
                   args=[self.academic_request_lecturer.id]),
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        if response.status_code == 200:
            response_data = json.loads(response.content)
            self.assertFalse(response_data['success'])
        else:
            self.assertIn(response.status_code, [302, 401, 403])
    
    def test_get_lecturer_requires_login(self):
        """Test that get lecturer API requires login"""
        response = self.client.get(reverse('get_lecturer'), {
            'subject': 'מבני נתונים'
        })
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)

class APIValidationTest(TestCase, TestDataMixin):
    """Test API input validation"""
    
    def setUp(self):
        self.client = Client()
        self.create_test_users()
        self.create_test_subjects()
    
    def test_submit_request_validates_required_fields(self):
        """Test that submit request validates required fields"""
        self.client.login(username='test_student', password='testpass123')
        
        # Test missing request_text
        data = {
            'request_type': 'ערעורים אקדמיים',
            'subject': 'מבני נתונים'
            # Missing request_text
        }
        
        response = self.client.post(reverse('submit_request'), data)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'error')
        self.assertIn('תאר את בקשתך', response_data['message'])
    
    def test_submit_request_validates_subject_for_lecturer_requests(self):
        """Test that submit request validates subject for lecturer requests"""
        self.client.login(username='test_student', password='testpass123')
        
        data = {
            'request_type': 'ערעורים אקדמיים',
            'request_text': 'Test request'
            # Missing subject for lecturer request
        }
        
        response = self.client.post(reverse('submit_request'), data)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'error')
        self.assertIn('בחר קורס', response_data['message'])
    
    def test_update_request_status_validates_status(self):
        """Test that update request status validates status values"""
        self.client.login(username='test_lecturer', password='testpass123')
        
        data = {
            'status': 'invalid_status',
            'lecturer_note': 'Test note',
            'request_type': 'academic'
        }
        
        response = self.client.post(
            reverse('lecturer_update_request_status', 
                   args=[self.academic_request_lecturer.id]),
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('תקין', response_data['message'])
    
    def test_personal_request_validates_lecturer_selection(self):
        """Test that personal request validates lecturer selection for recommendation letters"""
        self.client.login(username='test_student', password='testpass123')
        
        data = {
            'request_type': 'בקשה למכתבי המלצה',
            'request_text': 'I need a recommendation letter'
            # Missing selected_lecturer
        }
        
        response = self.client.post(reverse('submit_personal_requests'), data)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'error')
        self.assertIn('בחר מרצה', response_data['message'])

class APIErrorHandlingTest(TestCase, TestDataMixin):
    """Test API error handling"""
    
    def setUp(self):
        self.client = Client()
        self.create_test_users()
        self.create_test_requests()
    
    def test_update_nonexistent_request(self):
        """Test updating a nonexistent request"""
        self.client.login(username='test_lecturer', password='testpass123')
        
        data = {
            'status': 'approved',
            'lecturer_note': 'Test note',
            'request_type': 'academic'
        }
        
        response = self.client.post(
            reverse('lecturer_update_request_status', args=[99999]),
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('נמצא', response_data['message'])
    
    def test_get_lecturer_for_nonexistent_subject(self):
        """Test getting lecturer for nonexistent subject"""
        self.client.login(username='test_student', password='testpass123')
        
        response = self.client.get(reverse('get_lecturer'), {
            'subject': 'Completely Fake Subject'
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIsNone(data['lecturer_name'])
        self.assertIsNone(data['lecturer_id'])
    
    @patch('blog.views.AcademicRequest.objects.create')
    def test_database_error_handling(self, mock_create):
        """Test handling of database errors"""
        mock_create.side_effect = Exception('Database error')
        
        self.client.login(username='test_student', password='testpass123')
        
        data = {
            'request_type': 'ערעורים אקדמיים',
            'subject': 'מבני נתונים',
            'request_text': 'Test request'
        }
        
        response = self.client.post(reverse('submit_request'), data)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'error')
        self.assertIn('שגיאה', response_data['message'])

class APIPerformanceTest(TestCase, TestDataMixin):
    """Test API performance"""
    
    def setUp(self):
        self.client = Client()
        self.create_test_users()
        self.create_test_subjects()
    
    def test_get_lecturer_response_time(self):
        """Test get lecturer API response time"""
        self.client.login(username='test_student', password='testpass123')
        
        import time
        start_time = time.time()
        
        response = self.client.get(reverse('get_lecturer'), {
            'subject': 'מבני נתונים'
        })
        
        end_time = time.time()
        response_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        # API should respond within 1 second
        self.assertLess(response_time, 1.0)
    
    def test_submit_request_response_time(self):
        """Test submit request API response time"""
        self.client.login(username='test_student', password='testpass123')
        
        import time
        start_time = time.time()
        
        data = {
            'request_type': 'ערעורים אקדמיים',
            'subject': 'מבני נתונים',
            'request_text': 'Test request for performance'
        }
        
        response = self.client.post(reverse('submit_request'), data)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        # API should respond within 2 seconds
        self.assertLess(response_time, 2.0)

class APIConcurrencyTest(TestCase, TestDataMixin):
    """Test API concurrency handling"""
    
    def setUp(self):
        self.client = Client()
        self.create_test_users()
        self.create_test_requests()
    
    def test_concurrent_status_updates(self):
        """Test concurrent status updates on same request"""
        import threading
        import time
        
        self.client.login(username='test_lecturer', password='testpass123')
        
        results = []
        
        def update_status(status_value, note):
            client = Client()
            client.login(username='test_lecturer', password='testpass123')
            
            data = {
                'status': status_value,
                'lecturer_note': note,
                'request_type': 'academic'
            }
            
            response = client.post(
                reverse('lecturer_update_request_status', 
                       args=[self.academic_request_lecturer.id]),
                data,
                HTTP_X_REQUESTED_WITH='XMLHttpRequest'
            )
            
            results.append({
                'status_code': response.status_code,
                'response': json.loads(response.content),
                'attempted_status': status_value
            })
        
        # Create two threads trying to update simultaneously
        thread1 = threading.Thread(target=update_status, args=('in_progress', 'First update'))
        thread2 = threading.Thread(target=update_status, args=('approved', 'Second update'))
        
        thread1.start()
        thread2.start()
        
        thread1.join()
        thread2.join()
        
        # Both requests should complete successfully
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertEqual(result['status_code'], 200)
            self.assertTrue(result['response']['success'])
        
        # Final status should be one of the attempted statuses
        self.academic_request_lecturer.refresh_from_db()
        final_status = self.academic_request_lecturer.status
        attempted_statuses = [result['attempted_status'] for result in results]
        self.assertIn(final_status, attempted_statuses)