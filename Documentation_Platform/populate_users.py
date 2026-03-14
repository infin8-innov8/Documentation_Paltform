import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Documentation_Platform.settings')
django.setup()

from auth_autho.models import User, Department, Role

def create_user(full_name, email, role_name, dept_name=None):
    # generate username: firstname_lastname lowercase
    parts = full_name.split()
    if len(parts) >= 2:
        username = f"{parts[0].lower()}_{parts[-1].lower()}"
    else:
        username = parts[0].lower()

    try:
        role = Role.objects.get(role_name=role_name)
    except Role.DoesNotExist:
        print(f"Role {role_name} does not exist. Please run populate_roles_permissions.py first.")
        return
    
    dept = None
    if dept_name:
        dept, _ = Department.objects.get_or_create(department_name=dept_name)

    user, created = User.objects.get_or_create(email=email, defaults={
        'name': full_name,
        'username': username,
        'role': role,
        'department': dept,
        'is_active': True,
        'is_staff': True if role_name in ['President', 'Admin'] else False,
        'is_superuser': True if role_name in ['President', 'Admin'] else False
    })
    
    if created:
        user.set_password('defaultpassword') # Default password for new users
        user.save()
        print(f"Created user: {username} ({email}) with role: {role_name}" + (f" and department: {dept_name}" if dept_name else ""))
    else:
        print(f"User {username} already exists")

def run():
    print("Populating users...")
    create_user('Manas Vaijanath Deshmukh', 'manasdeshmukh512@gmail.com', 'President')
    create_user('Rutuja Jadhav', 'rutujajadhav475@gmail.com', 'Admin')
    create_user('Soham Santosh Tambe', 'sohamsantoshtambe5@gmail.com', 'Head of Department', 'Event Management')
    create_user('Pranav Mahendrapant Vasankar', 'pranav.vasankar@proton.me', 'Head of Department', 'Technical')
    create_user('Samarth Pravin Yete', 'yetesamarth@gmail.com', 'Head of Department', 'Documentation')
    print("Done populating users.")

if __name__ == '__main__':
    run()
