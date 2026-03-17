import os
import django
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Populate departments, roles, and link head users to their departments.'

    def handle(self, *args, **options):
        from auth_autho.models import User, Department, Role, Permission

        # 1) Create Roles
        roles_data = ['President', 'Admin', 'Head of Department']
        for r_name in roles_data:
            role, created = Role.objects.get_or_create(role_name=r_name)
            if created:
                role.description = f'{r_name} role'
                role.save()
                self.stdout.write(self.style.SUCCESS(f'Created role: {r_name}'))
            else:
                self.stdout.write(f'Role already exists: {r_name}')

        # 2) Create Permissions
        perms = ['Modify documents', 'view documents', 'upload documents', 'delete documents']
        for p_name in perms:
            perm, created = Permission.objects.get_or_create(name=p_name)
            if created:
                perm.description = f'Permission to {p_name.lower()}'
                perm.save()
                self.stdout.write(self.style.SUCCESS(f'Created permission: {p_name}'))

        # 3) Create Departments
        departments_data = [
            {'name': 'Event Management', 'desc': 'Manages all club events, planning, and execution.'},
            {'name': 'Technical', 'desc': 'Handles technical projects, workshops, and bootcamps.'},
            {'name': 'Documentation', 'desc': 'Manages meeting minutes, reports, and official documentation.'},
        ]
        for d in departments_data:
            dept, created = Department.objects.get_or_create(
                department_name=d['name'],
                defaults={'description': d['desc']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created department: {d["name"]}'))
            else:
                self.stdout.write(f'Department already exists: {d["name"]}')

        # 4) Create users and link to departments
        head_role = Role.objects.get(role_name='Head of Department')
        president_role = Role.objects.get(role_name='President')
        admin_role = Role.objects.get(role_name='Admin')

        users_data = [
            {'name': 'Manas Vaijanath Deshmukh', 'email': 'manasdeshmukh512@gmail.com', 'role': president_role, 'dept': None},
            {'name': 'Rutuja Jadhav', 'email': 'rutujajadhav475@gmail.com', 'role': admin_role, 'dept': None},
            {'name': 'Soham Santosh Tambe', 'email': 'sohamsantoshtambe5@gmail.com', 'role': head_role, 'dept': 'Event Management'},
            {'name': 'Pranav Mahendrapant Vasankar', 'email': 'pranav.vasankar@proton.me', 'role': head_role, 'dept': 'Technical'},
            {'name': 'Samarth Pravin Yete', 'email': 'yetesamarth@gmail.com', 'role': head_role, 'dept': 'Documentation'},
        ]

        for u_data in users_data:
            dept = None
            if u_data['dept']:
                dept = Department.objects.get(department_name=u_data['dept'])

            parts = u_data['name'].split()
            username = f"{parts[0].lower()}_{parts[-1].lower()}" if len(parts) >= 2 else parts[0].lower()

            # Try to find existing user by email OR username
            user = User.objects.filter(email=u_data['email']).first()
            if not user:
                user = User.objects.filter(username=username).first()

            if user:
                # Update existing user's department and role
                changed = False
                if dept and user.department != dept:
                    user.department = dept
                    changed = True
                if u_data['role'] and user.role != u_data['role']:
                    user.role = u_data['role']
                    changed = True
                if changed:
                    user.save()
                    self.stdout.write(self.style.WARNING(f'Updated user: {user.username} → dept={dept}, role={u_data["role"]}'))
                else:
                    self.stdout.write(f'User already correct: {user.username} (dept={user.department}, role={user.role})')
            else:
                # Create new user
                user = User.objects.create(
                    name=u_data['name'],
                    username=username,
                    email=u_data['email'],
                    role=u_data['role'],
                    department=dept,
                    is_active=True,
                    is_staff=u_data['role'].role_name in ['President', 'Admin'],
                    is_superuser=u_data['role'].role_name in ['President', 'Admin'],
                )
                user.set_password('defaultpassword')
                user.save()
                self.stdout.write(self.style.SUCCESS(
                    f'Created user: {username} ({u_data["role"].role_name})' +
                    (f' → {u_data["dept"]}' if u_data['dept'] else '')
                ))

        self.stdout.write(self.style.SUCCESS('\n✅ All departments, roles, and users are set up!'))
