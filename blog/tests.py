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

class StudentRequestTests(TestCase):
    def test_student_request_str(self):
        request = StudentRequest.objects.create(
            username="student123",
            category="General",
            request_type="Document Upload",
            text="Please upload my document"
        )
        self.assertIn("student123", str(request))

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
