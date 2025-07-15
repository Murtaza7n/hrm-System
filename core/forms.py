from django import forms
from .models import Client, Project, Employee, Department, Task, BudgetCategory, Budget, BudgetExpense, BudgetRevenue, Asset, CompanySettings, LocalizationSettings, InvoiceSettings, SalarySettings, ThemeSettings, Tax, Expense, Estimate, EstimateItem, Invoice, InvoiceItem
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

class BudgetCategoryForm(forms.ModelForm):
    class Meta:
        model = BudgetCategory
        fields = ['name', 'description'] 

class BudgetForm(forms.ModelForm):
    period_start = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    period_end = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    class Meta:
        model = Budget
        fields = ['type', 'name', 'category', 'project', 'tax', 'period_start', 'period_end', 'attachment', 'note'] 

class BudgetExpenseForm(forms.ModelForm):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), required=False)
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), required=False)
    class Meta:
        model = BudgetExpense
        fields = ['title', 'budget', 'amount', 'description', 'start_date', 'end_date', 'attachment'] 

class BudgetRevenueForm(forms.ModelForm):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), required=False)
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), required=False)
    class Meta:
        model = BudgetRevenue
        fields = ['title', 'budget', 'amount', 'description', 'start_date', 'end_date', 'attachment'] 

class AssetForm(forms.ModelForm):
    purchase_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), required=False)
    warranty_end = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), required=False)
    class Meta:
        model = Asset
        fields = ['asset_name', 'asset_id', 'purchase_date', 'purchase_from', 'manufacturer', 'model', 'serial_number', 'brand', 'supplier', 'condition', 'warranty', 'warranty_end', 'cost', 'asset_user', 'status', 'description', 'files']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'asset_user': forms.Select(attrs={'class': 'form-control'}),
        } 

class CompanySettingsForm(forms.ModelForm):
    class Meta:
        model = CompanySettings
        fields = ['company_name', 'contact_person', 'address', 'country', 'city', 'state_province', 'postal_code', 'email', 'phone_number', 'mobile_number', 'fax', 'website_url'] 

class LocalizationSettingsForm(forms.ModelForm):
    class Meta:
        model = LocalizationSettings
        fields = ['default_language', 'timezone', 'date_format', 'time_format', 'currency', 'currency_symbol', 'thousand_separator', 'decimal_separator'] 

class InvoiceSettingsForm(forms.ModelForm):
    class Meta:
        model = InvoiceSettings
        fields = ['prefix', 'logo']
        widgets = {
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        } 

class SalarySettingsForm(forms.ModelForm):
    class Meta:
        model = SalarySettings
        fields = [
            'da_enabled', 'da_percent', 'hra_enabled', 'hra_percent',
            'pf_enabled', 'pf_employee_share', 'pf_org_share',
            'esi_enabled', 'esi_employee_share', 'esi_org_share',
            'gratuity_enabled', 'gratuity_employee_share', 'gratuity_org_share',
        ]
        widgets = {
            'da_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
            'hra_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
            'pf_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
            'esi_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
            'gratuity_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
            'da_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'hra_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'pf_employee_share': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'pf_org_share': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'esi_employee_share': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'esi_org_share': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'gratuity_employee_share': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'gratuity_org_share': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        } 

class ThemeSettingsForm(forms.ModelForm):
    class Meta:
        model = ThemeSettings
        fields = [
            'app_name', 'logo_light', 'logo_dark', 'favicon',
            'layout', 'layout_width', 'color_scheme', 'layout_position',
            'topbar_color', 'sidebar_size', 'sidebar_view', 'sidebar_color',
        ]
        widgets = {
            'logo_light': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'logo_dark': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'favicon': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'layout': forms.Select(attrs={'class': 'form-select'}),
            'layout_width': forms.Select(attrs={'class': 'form-select'}),
            'color_scheme': forms.Select(attrs={'class': 'form-select'}),
            'layout_position': forms.Select(attrs={'class': 'form-select'}),
            'topbar_color': forms.Select(attrs={'class': 'form-select'}),
            'sidebar_size': forms.Select(attrs={'class': 'form-select'}),
            'sidebar_view': forms.Select(attrs={'class': 'form-select'}),
            'sidebar_color': forms.Select(attrs={'class': 'form-select'}),
        } 

class TaxForm(forms.ModelForm):
    class Meta:
        model = Tax
        fields = ['name', 'percentage', 'active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter tax name'}),
            'percentage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter percentage: 10', 'step': '0.01'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        } 

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['item_name', 'purchased_from', 'purchased_date', 'amount', 'paid_by', 'status']
        widgets = {
            'item_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Item Name'}),
            'purchased_from': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Purchased From'}),
            'purchased_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Amount', 'step': '0.01'}),
            'paid_by': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Paid By'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        } 

class EstimateForm(forms.ModelForm):
    class Meta:
        model = Estimate
        fields = ['client', 'project', 'tax', 'client_address', 'billing_address', 'estimate_date', 'expiry_date', 'discount', 'other_info']
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select'}),
            'project': forms.Select(attrs={'class': 'form-select'}),
            'tax': forms.Select(attrs={'class': 'form-select'}),
            'client_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'billing_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'estimate_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'other_info': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class EstimateItemForm(forms.ModelForm):
    class Meta:
        model = EstimateItem
        fields = ['item', 'description', 'unit_cost', 'quantity', 'amount']
        widgets = {
            'item': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Item'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Description'}),
            'unit_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '1', 'min': '1'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        } 

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['client', 'project', 'tax', 'client_address', 'billing_address', 'invoice_date', 'due_date', 'discount', 'other_info', 'status']
        widgets = {
            'invoice_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['item', 'description', 'unit_cost', 'quantity', 'amount'] 