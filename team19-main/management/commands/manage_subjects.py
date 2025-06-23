# # management/commands/manage_subjects.py
# # Create this file in: your_app/management/commands/manage_subjects.py

# from django.core.management.base import BaseCommand
# from django.contrib.auth import get_user_model
# from users.models import Subject

# User = get_user_model()

# class Command(BaseCommand):
#     help = 'Manage subjects and check database status'

#     def add_arguments(self, parser):
#         parser.add_argument(
#             '--action',
#             type=str,
#             choices=['check', 'create_sample', 'list_all'],
#             default='check',
#             help='Action to perform'
#         )

#     def handle(self, *args, **options):
#         action = options['action']

#         if action == 'check':
#             self.check_database()
#         elif action == 'create_sample':
#             self.create_sample_data()
#         elif action == 'list_all':
#             self.list_all_subjects()

#     def check_database(self):
#         """Check the current state of subjects and users"""
#         self.stdout.write(self.style.SUCCESS('=== Database Check ==='))
        
#         # Check users
#         total_users = User.objects.count()
#         lecturers = User.objects.filter(is_lecturer=True)
#         students = User.objects.filter(is_student=True)
        
#         self.stdout.write(f'Total users: {total_users}')
#         self.stdout.write(f'Lecturers: {lecturers.count()}')
#         self.stdout.write(f'Students: {students.count()}')
        
#         # Check subjects
#         total_subjects = Subject.objects.count()
#         self.stdout.write(f'Total subjects: {total_subjects}')
        
#         # Check subjects by department
#         departments = ['מדעי המחשב', 'הנדסת תוכנה', 'הנדסת אלקטרוניקה']
#         for dept in departments:
#             dept_subjects = Subject.objects.filter(department=dept)
#             self.stdout.write(f'Subjects in {dept}: {dept_subjects.count()}')
        
#         # List lecturers and their subjects
#         self.stdout.write('\n=== Lecturers and Subjects ===')
#         for lecturer in lecturers:
#             lecturer_subjects = Subject.objects.filter(lecturer=lecturer)
#             self.stdout.write(f'{lecturer.username} ({lecturer.department}): {lecturer_subjects.count()} subjects')
#             for subject in lecturer_subjects:
#                 self.stdout.write(f'  - {subject.name}')

#     def create_sample_data(self):
#         """Create sample subjects for testing"""
#         self.stdout.write(self.style.SUCCESS('=== Creating Sample Data ==='))
        
#         # First, create sample lecturers if they don't exist
#         departments = {
#             'מדעי המחשב': ['אלגוריתמים', 'מבני נתונים', 'תכנות מונחה עצמים'],
#             'הנדסת תוכנה': ['הנדסת תוכנה', 'בדיקות תוכנה', 'ניהול פרויקטים'],
#             'הנדסת אלקטרוניקה': ['מעגלים דיגיטליים', 'אלקטרוניקה אנלוגית', 'מערכות בקרה']
#         }
        
#         for dept, subjects in departments.items():
#             # Create a lecturer for this department if none exists
#             lecturer = User.objects.filter(department=dept, is_lecturer=True).first()
#             if not lecturer:
#                 lecturer = User.objects.create_user(
#                     username=f'lecturer_{dept.replace(" ", "_")}',
#                     email=f'lecturer_{dept.replace(" ", "_")}@example.com',
#                     first_name='מר',
#                     last_name=f'מרצה {dept}',
#                     department=dept,
#                     is_lecturer=True,
#                     is_approved=True
#                 )
#                 self.stdout.write(f'Created lecturer: {lecturer.username}')
            
#             # Create subjects for this lecturer
#             for subject_name in subjects:
#                 subject, created = Subject.objects.get_or_create(
#                     name=subject_name,
#                     department=dept,
#                     defaults={'lecturer': lecturer}
#                 )
#                 if created:
#                     self.stdout.write(f'Created subject: {subject_name} for {lecturer.username}')
#                 else:
#                     self.stdout.write(f'Subject already exists: {subject_name}')

#     def list_all_subjects(self):
#         """List all subjects with details"""
#         self.stdout.write(self.style.SUCCESS('=== All Subjects ==='))
        
#         subjects = Subject.objects.select_related('lecturer').order_by('department', 'name')
        
#         current_dept = None
#         for subject in subjects:
#             if subject.department != current_dept:
#                 current_dept = subject.department
#                 self.stdout.write(f'\n{current_dept}:')
#                 self.stdout.write('-' * 40)
            
#             lecturer_name = f'{subject.lecturer.first_name} {subject.lecturer.last_name}'.strip()
#             if not lecturer_name:
#                 lecturer_name = subject.lecturer.username
            
#             self.stdout.write(f'  {subject.name} - {lecturer_name}')

# # Alternative: Quick script you can run in Django shell
# """
# To run this in Django shell (python manage.py shell):

# from django.contrib.auth import get_user_model
# from users.models import Subject

# User = get_user_model()

# # Check current subjects
# print("Current subjects:")
# for subject in Subject.objects.all():
#     print(f"- {subject.name} ({subject.department}) - {subject.lecturer}")

# # Create sample subjects if needed
# dept = 'מדעי המחשב'  # Your user's department
# lecturer = User.objects.filter(department=dept, is_lecturer=True).first()

# if lecturer:
#     subjects_to_create = ['מבני נתונים', 'אלגוריתמים', 'תכנות מונחה עצמים']
#     for subject_name in subjects_to_create:
#         subject, created = Subject.objects.get_or_create(
#             name=subject_name,
#             department=dept,
#             defaults={'lecturer': lecturer}
#         )
#         print(f"Subject {subject_name}: {'created' if created else 'already exists'}")
# else:
#     print("No lecturer found for department:", dept)
# """