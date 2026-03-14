import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Documentation_Platform.settings')
django.setup()

from auth_autho.models import Role, Permission

def run():
    roles = ['President', 'Admin', 'Head of Department']
    permissions = ['Remove documents', 'Modify documents', 'view documents']

    for r in roles:
        role, created = Role.objects.get_or_create(role_name=r)
        if created:
            role.description = f'{r} role'
            role.save()
            print(f"Created role: {r}")

    for p in permissions:
        perm, created = Permission.objects.get_or_create(name=p)
        if created:
            perm.description = f'Permission to {p.lower()}'
            perm.save()
            print(f"Created permission: {p}")

    print("Roles and Permissions populated successfully.")

if __name__ == '__main__':
    run()
