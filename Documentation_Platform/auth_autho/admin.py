from django.contrib import admin
from .models import User, Department, Role, Permission, RolePermission

admin.site.register(User)
admin.site.register(Department)
admin.site.register(Role)
admin.site.register(Permission)
admin.site.register(RolePermission)
