from django.core.management.base import BaseCommand
from core.models import User, Role, Leave

class Command(BaseCommand):
    def handle(self, *args, **kwargs):

        # Create roles first
        admin_role, _ = Role.objects.get_or_create(role_name='ADMIN')
        manager_role, _ = Role.objects.get_or_create(role_name='MANAGER')
        employee_role, _ = Role.objects.get_or_create(role_name='EMPLOYEE')

        # Create users with Role instances
        admin = User.objects.create_user(
            email='admin@hrms.com',
            password='admin123',
            role=admin_role,
            name='Admin User'
        )

        manager = User.objects.create_user(
            email='manager@hrms.com',
            password='manager123',
            role=manager_role,
            name='Manager User'
        )

        employee = User.objects.create_user(
            email='emp@hrms.com',
            password='emp123',
            role=employee_role,
            name='Employee User',
            manager=manager
        )

        # Sample leave
        Leave.objects.create(
            user=employee,
            leave_type='CASUAL',
            start_date='2026-01-10',
            end_date='2026-01-12',
            reason='Personal work'
        )

        self.stdout.write(self.style.SUCCESS('Database seeded successfully'))
