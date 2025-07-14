from core.models import Permission

# List of default permissions
permissions = [
    'View Attendance',
    'Edit Attendance',
    'View Employee',
    'Edit Employee',
    'View Payroll',
    'Edit Payroll',
    'View Leaves',
    'Approve Leaves',
    'View Roles',
    'Edit Roles',
]

for perm_name in permissions:
    Permission.objects.get_or_create(name=perm_name)

print('Default permissions have been added.') 