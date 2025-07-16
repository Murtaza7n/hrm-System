from django import template
from core.models import EmployeePermission

register = template.Library()

@register.filter
def dict_get(d, key):
    if d is None:
        return None
    return d.get(key)

# Utility function for views
def user_has_permission(user, module, action):
    try:
        emp = user.employee
        perm = EmployeePermission.objects.get(employee=emp, module=module, action=action)
        return perm.allowed and not perm.locked
    except EmployeePermission.DoesNotExist:
        return False
    except Exception:
        return False

# Template filter for permission check
@register.simple_tag(takes_context=True)
def has_permission(context, module, action):
    user = context['user']
    return user_has_permission(user, module, action) 