from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import ChatHistory, StudentRequest, AcademicRequest
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class ChatHistoryTests(TestCase):
    def test_chat_history_str(self):
        chat = ChatHistory.objects.create(
            username="maysa",
            message="Hello",
            reply="Hi there!"
        )
        self.assertIn("maysa", str(chat))

# class StudentRequestTests(TestCase):
#     def test_student_request_str(self):
#         request = StudentRequest.objects.create(
#             username="student123",
#             category="General",
#             request_type="Document Upload",
#             text="Please upload my document"
#         )
#         self.assertIn("student123", str(request))

class AcademicRequestTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="maysa", password="pass123")

    def test_academic_request_str(self):
        req = AcademicRequest.objects.create(
            student=self.user,
            subject="Algorithms",
            request_type="Extension",
            request_text="Need more time",
            status="pending"
        )
        self.assertIn("Algorithms", str(req))
        self.assertEqual(req.status, "pending")

    def test_is_past_deadline_true(self):
        req = AcademicRequest.objects.create(
            student=self.user,
            subject="Math",
            request_type="Update",
            request_text="Please update",
            status="need_update",
            update_deadline=timezone.now() - timedelta(days=1)
        )
        self.assertTrue(req.is_past_deadline())

    def test_is_past_deadline_false(self):
        req = AcademicRequest.objects.create(
            student=self.user,
            subject="Math",
            request_type="Update",
            request_text="Still valid",
            status="in_progress",
            update_deadline=timezone.now() + timedelta(days=1)
        )
        self.assertFalse(req.is_past_deadline())






#tests for technaicl machine 

class ErrorReportFormTests(TestCase):

    def setUp(self):
        self.url = reverse('error_report')  # replace with your actual URL name

    def test_valid_form_submission(self):
        """
        ✅ Should accept a valid form submission with required fields.
        """
        data = {
            'name': 'Yazed User',
            'email': 'yazed@ac.sce.ac.il',
            'errorType': 'UI Bug',
            'description': 'The submit button is misaligned.',
            'urgency': 'High'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        
        # Check hidden div exists but with empty array
        self.assertContains(response, '<div id="requestsData" data-requests="[]"')
        
    def test_view_button_has_correct_attributes(self):
        """POSITIVE TEST: Verify view buttons have correct data attributes"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('request-list'))  # Update with your URL name
        
        self.assertEqual(response.status_code, 200)
        
        # Check view button exists with correct data attribute
        self.assertContains(
            response, 
            f'class="view-request-btn" data-request-id="{self.pending_request.id}"'
        )
        self.assertContains(
            response,
            f'href="/request/view/{self.pending_request.id}/"'
        )

    def test_page_with_invalid_request_status(self):
        """NEGATIVE TEST: Verify page handles invalid status gracefully"""
        # Create request with invalid status
        invalid_request = AcademicRequest.objects.create(
            title="Invalid Status Request",
            status="invalid_status",
            created_by=self.user
        )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('request-list')))
        
        self.assertEqual(response.status_code, 200)
        
        # Page should still render without errors
        self.assertContains(response, f'"id": {invalid_request.id}')
        self.assertContains(response, f'"status": "invalid_status"')