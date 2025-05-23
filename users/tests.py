from django.test import TestCase

from django.contrib.auth import get_user_model
from users.models import Profile, LecturerProfile

User = get_user_model()

class UserModelTests(TestCase):
    def test_create_student_user(self):
        user = User.objects.create_user(username='student1', password='testpass123', is_student=True)
        self.assertTrue(user.is_student)
        self.assertFalse(user.is_lecturer)
        self.assertEqual(user.username, 'student1')

    def test_create_lecturer_user(self):
        user = User.objects.create_user(username='lecturer1', password='testpass123', is_lecturer=True)
        self.assertTrue(user.is_lecturer)
        self.assertFalse(user.is_student)
        self.assertEqual(user.username, 'lecturer1')

class ProfileModelTests(TestCase):
    def test_profile_creation(self):
        user = User.objects.create_user(username='user1', password='pass')
        profile = Profile.objects.create(user=user)
        self.assertEqual(str(profile), 'user1 Profile')

# class LecturerProfileModelTests(TestCase):
#     def test_lecturer_profile_str(self):
#         user = User.objects.create_user(username='lecturer2', password='pass', first_name='Lec', last_name='Name')
#         lecturer_profile = LecturerProfile.objects.create(user=user, subject='Cyber Security')
#         self.assertEqual(str(lecturer_profile), 'Lec Name - Cyber Security')


from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

class FileUploadTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('upload_document')  # Make sure this name exists in urls.py

    def test_upload_valid_pdf_file(self):
        """✅ Positive test: Uploads a valid PDF file and expects a 200 or redirect"""
        file = SimpleUploadedFile("test.pdf", b"file_content", content_type="application/pdf")
        response = self.client.post(self.url, {
            'document_type': 'transcript',
            'pdf_file': file
        })

        self.assertIn(response.status_code, [200, 302], "Expected success status on valid upload.")

    def test_upload_without_file(self):
        """❌ Negative test: Submit form without file should return form error"""
        response = self.client.post(self.url, {
            'document_type': 'transcript'
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required", msg_prefix="Should return error for missing file")

from .models import RequestModel

class RequestDetailViewTests(TestCase):
    def setUp(self):
        # Request with update deadline in the future
        self.request_with_deadline = RequestModel.objects.create(
            student_name="Alice",
            subject="Math",
            request_type="Exam Help",
            created_at=timezone.now(),
            request_text="I need help with question 2.",
            lecturer_note="Pending review",
            status="pending",
            update_deadline=timezone.now().date() + timezone.timedelta(days=3)
        )
        # Request without an update deadline
        self.request_without_deadline = RequestModel.objects.create(
            student_name="Bob",
            subject="Science",
            request_type="Lab Report",
            created_at=timezone.now(),
            request_text="Please review my lab report.",
            lecturer_note="Reviewed",
            status="approved",
            update_deadline=None
        )

    def test_get_request_detail_success_with_deadline(self):
        """✅ Positive test: valid request with deadline returns correct JSON"""
        url = reverse('request_detail', args=[self.request_with_deadline.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['id'], self.request_with_deadline.id)
        self.assertEqual(data['student_name'], "Alice")
        self.assertIsNotNone(data['update_deadline'])
        self.assertFalse(data['is_past_deadline'])

    def test_get_request_detail_success_without_deadline(self):
        """✅ Positive test: valid request without deadline returns correct JSON"""
        url = reverse('request_detail', args=[self.request_without_deadline.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['id'], self.request_without_deadline.id)
        self.assertEqual(data['student_name'], "Bob")
        self.assertIsNone(data['update_deadline'])

    def test_get_request_detail_not_found(self):
        """❌ Negative test: invalid request ID returns 404"""
        url = reverse('request_detail', args=[9999])  # ID not existing
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_post_request_detail_not_allowed(self):
        """❌ Negative test: POST method not allowed on this endpoint"""
        url = reverse('request_detail', args=[self.request_with_deadline.id])
        response = self.client.post(url)
        self.assertIn(response.status_code, [405, 404])  # 405 Method Not Allowed or 404 if not defined
 
 from django.urls import reverse

class RegistrationFormTests(TestCase):
    def setUp(self):
        self.url = reverse('register')  # Adjust to your register URL name

    def test_register_with_student_role_selected(self):
        """✅ Positive: Submit form with student role selected"""
        response = self.client.post(self.url, {
            'hidden_is_student': 'True',
            'hidden_is_lecturer': 'False',
            # other required form fields here...
        })
        self.assertEqual(response.status_code, 302)  # Assuming redirect on success
        # Could check for successful user creation or redirect location

    def test_register_with_lecturer_role_selected(self):
        """✅ Positive: Submit form with lecturer role selected"""
        response = self.client.post(self.url, {
            'hidden_is_student': 'False',
            'hidden_is_lecturer': 'True',
            # other required form fields here...
        })
        self.assertEqual(response.status_code, 302)  # Assuming redirect on success

    def test_register_with_no_role_selected(self):
        """❌ Negative: Submit form with no role selected should return form error"""
        response = self.client.post(self.url, {
            'hidden_is_student': 'False',
            'hidden_is_lecturer': 'False',
            # other required form fields here...
        })
        self.assertEqual(response.status_code, 200)  # Form redisplayed with errors
        self.assertContains(response, 'אנא בחר תפקיד אחד (סטודנט או מרצה)')

    def test_register_get_request(self):
        """❌ Negative: GET request to register returns form page"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<form')  # Form is present in the HTML