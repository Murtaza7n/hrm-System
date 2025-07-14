from django import forms
from .models import Client, Project, Employee, Department, Task
from django.contrib.auth.models import User
from django.utils.html import format_html

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'email', 'phone', 'address', 'company', 'description']

class UserAdminForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=False)
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password', 'is_active', 'is_staff', 'is_superuser']

class GroupedEmployeeChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.user.get_full_name() or obj.user.username} ({obj.department.name}, {obj.designation.name})"

class GroupedCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    def optgroups(self, name, value, attrs=None):
        # Group employees by department
        employees = self.choices.queryset.select_related('department', 'designation')
        department_map = {}
        for emp in employees:
            dept = emp.department.name if emp.department else 'No Department'
            department_map.setdefault(dept, []).append(emp)
        groups = []
        for dept, emps in sorted(department_map.items()):
            group_choices = [(emp.pk, str(emp), emp.pk in value) for emp in emps]
            groups.append((dept, group_choices, 0))
        return groups

class ProjectForm(forms.ModelForm):
    manager = forms.ModelChoiceField(
        queryset=Employee.objects.none(),  # Will be set in __init__
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
        label='Project Manager',
        to_field_name=None,
    )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only employees with designation 'Project Manager'
        self.fields['manager'].queryset = Employee.objects.select_related('department', 'designation').filter(designation__name='Project Manager')
        self.fields['manager'].label_from_instance = lambda obj: f"{obj.user.get_full_name() or obj.user.username} ({obj.department.name}, {obj.designation.name}) - Project Manager"

    class Meta:
        model = Project
        fields = ['name', 'client', 'manager']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'client': forms.Select(attrs={'class': 'form-control', 'data-live-search': 'true'}),
        }

class TaskForm(forms.ModelForm):
    deadline = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), required=False)
    priority = forms.ChoiceField(choices=Task.PRIORITY_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}), required=False)
    attachment = forms.FileField(widget=forms.ClearableFileInput(attrs={'class': 'form-control'}), required=False)
    comment = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}), required=False)
    class Meta:
        model = Task
        fields = ['assigned_to', 'title', 'description', 'deadline', 'priority', 'attachment', 'comment']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
        }
    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        manager = kwargs.pop('manager', None)
        super().__init__(*args, **kwargs)
        # Only show employees who are not the manager
        if manager:
            self.fields['assigned_to'].queryset = Employee.objects.exclude(id=manager.id)
        else:
            self.fields['assigned_to'].queryset = Employee.objects.all() 