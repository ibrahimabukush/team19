from django.core.management.base import BaseCommand
from users.models import User

class Command(BaseCommand):
    help = 'Create secretary users for all departments'

    def handle(self, *args, **kwargs):
        # Secretary data with usernames and passwords
        secretaries_data = [
            {
                'username': 'maya_secretary',
                'password': 'Maya2024!',
                'email': 'maya.secretary@sce.ac.il',
                'first_name': 'Maya',
                'last_name': 'Cohen',
                'department': 'sw_engineering',
            },
            {
                'username': 'sarah_secretary',
                'password': 'Sarah2024!',
                'email': 'sarah.secretary@sce.ac.il',
                'first_name': 'Sarah',
                'last_name': 'Levy',
                'department': 'cs_engineering',
            },
            {
                'username': 'rachel_secretary',
                'password': 'Rachel2024!',
                'email': 'rachel.secretary@sce.ac.il',
                'first_name': 'Rachel',
                'last_name': 'Mizrahi',
                'department': 'ee_engineering',
            }
        ]
        
        for sec_data in secretaries_data:
            # Create or update user
            user, created = User.objects.update_or_create(
                username=sec_data['username'],
                defaults={
                    'email': sec_data['email'],
                    'first_name': sec_data['first_name'],
                    'last_name': sec_data['last_name'],
                    'is_secretary': True,
                    'department': sec_data['department'],
                    'is_approved': True,
                    'is_active': True,
                }
            )
            
            if created:
                user.set_password(sec_data['password'])
                user.save()
                self.stdout.write(f"Created user: {user.username}")
            else:
                self.stdout.write(f"Updated user: {user.username}")
        
        self.stdout.write(self.style.SUCCESS('Successfully created/updated all secretaries'))
        
        # Print login credentials
        self.stdout.write("\n" + "="*50)
        self.stdout.write("SECRETARY LOGIN CREDENTIALS")
        self.stdout.write("="*50)
        for sec_data in secretaries_data:
            dept_name = {
                'sw_engineering': 'Software Engineering',
                'cs_engineering': 'Computer Science',
                'ee_engineering': 'Electronic Engineering'
            }.get(sec_data['department'], sec_data['department'])
            
            self.stdout.write(f"\nDepartment: {dept_name}")
            self.stdout.write(f"Username: {sec_data['username']}")
            self.stdout.write(f"Password: {sec_data['password']}")
            self.stdout.write(f"Email: {sec_data['email']}")
            self.stdout.write("-"*30)