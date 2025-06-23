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

