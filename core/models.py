from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings

# Create your models here.

class Department(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Designation(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    designation = models.ForeignKey('Designation', on_delete=models.SET_NULL, null=True, blank=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    date_of_joining = models.DateField(null=True, blank=True)

    def __str__(self):
        return str(self.user)

class ChatMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.sender} to {self.recipient}: {self.content[:20]}"

class Ticket(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('closed', 'Closed'),
    ]
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets_created')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets_assigned')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.status})"

class OnlineUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='online_status')
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} (online)"

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'date')

    def __str__(self):
        return f"{self.user} - {self.date} ({self.status})"

# SalarySlip model removed. PayrollItem and Payslip models will be added.

class Holiday(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateField()
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"{self.name} ({self.date})"

class Leave(models.Model):
    LEAVE_TYPE_CHOICES = [
        ('sick', 'Sick Leave'),
        ('casual', 'Casual Leave'),
        ('earned', 'Earned Leave'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPE_CHOICES)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_leaves')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    comments = models.TextField(blank=True)

    class Meta:
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.employee} {self.leave_type} {self.start_date} - {self.end_date}"

class PayrollItem(models.Model):
    EARNING = 'earning'
    DEDUCTION = 'deduction'
    ITEM_TYPE_CHOICES = [
        (EARNING, 'Earning'),
        (DEDUCTION, 'Deduction'),
    ]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payroll_items')
    date = models.DateField(default=timezone.now)
    name = models.CharField(max_length=100)
    item_type = models.CharField(max_length=10, choices=ITEM_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.item_type})"

class Payslip(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payslip: {str(self.employee)} - {self.date}"

    def get_payroll_items(self):
        from .models import PayrollItem
        return PayrollItem.objects.filter(employee=self.employee)

class Client(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    company = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Project(models.Model):
    name = models.CharField(max_length=200)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='projects')
    manager = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_projects')
    # team = models.ManyToManyField(Employee, related_name='projects')  # Remove or comment out

    def __str__(self):
        return self.name

class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    assigned_by = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='tasks_assigned')
    assigned_to = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='tasks_received')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    deadline = models.DateField(null=True, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    attachment = models.FileField(upload_to='task_attachments/', null=True, blank=True)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.status}) for {self.assigned_to}"

class BudgetCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Budget(models.Model):
    TYPE_CHOICES = [
        ('project', 'Project'),
        ('category', 'Category'),
    ]
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='project')
    name = models.CharField(max_length=100)
    category = models.ForeignKey(BudgetCategory, on_delete=models.CASCADE, related_name='budgets', null=True, blank=True)
    project = models.ForeignKey('Project', on_delete=models.SET_NULL, null=True, blank=True, related_name='budgets')
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    period_start = models.DateField()
    period_end = models.DateField()
    attachment = models.FileField(upload_to='budget_attachments/', null=True, blank=True)
    note = models.TextField(blank=True)
    # amount is now calculated, not user input

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"

class BudgetExpense(models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='expenses')
    title = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    date = models.DateField(default=timezone.now)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    attachment = models.FileField(upload_to='budget_expense_attachments/', null=True, blank=True)

    def __str__(self):
        return f"Expense: {self.title} ({self.amount}) for {self.budget.name}"

class BudgetRevenue(models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='revenues')
    title = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    date = models.DateField(default=timezone.now)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    attachment = models.FileField(upload_to='budget_revenue_attachments/', null=True, blank=True)

    def __str__(self):
        return f"Revenue: {self.title} ({self.amount}) for {self.budget.name}"

class Asset(models.Model):
    STATUS_CHOICES = [
        ('approved', 'Approved'),
        ('pending', 'Pending'),
        ('returned', 'Returned'),
    ]
    asset_name = models.CharField(max_length=255)
    asset_id = models.CharField(max_length=100, unique=True)
    purchase_date = models.DateField(null=True, blank=True)
    purchase_from = models.CharField(max_length=255, blank=True)
    manufacturer = models.CharField(max_length=255, blank=True)
    model = models.CharField(max_length=255, blank=True)
    serial_number = models.CharField(max_length=255, blank=True)
    brand = models.CharField(max_length=255, blank=True)
    supplier = models.CharField(max_length=255, blank=True)
    condition = models.CharField(max_length=255, blank=True)
    warranty = models.CharField(max_length=100, blank=True)
    warranty_end = models.DateField(null=True, blank=True)
    cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    asset_user = models.ForeignKey('Employee', on_delete=models.SET_NULL, null=True, blank=True, related_name='assets')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='approved')
    description = models.TextField(blank=True)
    files = models.FileField(upload_to='asset_files/', null=True, blank=True)

    def __str__(self):
        return f"{self.asset_name} ({self.asset_id})"

class CompanySettings(models.Model):
    company_name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True)
    address = models.TextField(blank=True)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state_province = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=30, blank=True)
    mobile_number = models.CharField(max_length=30, blank=True)
    fax = models.CharField(max_length=30, blank=True)
    website_url = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.company_name or 'Company Settings'

class LocalizationSettings(models.Model):
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('ur', 'Urdu'),
        ('ar', 'Arabic'),
        # Add more as needed
    ]
    TIMEZONE_CHOICES = [
        ('Asia/Karachi', 'Asia/Karachi'),
        ('Asia/Dubai', 'Asia/Dubai'),
        ('UTC', 'UTC'),
        # Add more as needed
    ]
    default_language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='en')
    timezone = models.CharField(max_length=50, choices=TIMEZONE_CHOICES, default='Asia/Karachi')
    date_format = models.CharField(max_length=20, default='%Y-%m-%d')
    time_format = models.CharField(max_length=20, default='%H:%M')
    currency = models.CharField(max_length=10, default='PKR')
    currency_symbol = models.CharField(max_length=5, default='₨')
    thousand_separator = models.CharField(max_length=2, default=',')
    decimal_separator = models.CharField(max_length=2, default='.')

    def __str__(self):
        return f"Localization ({self.default_language}, {self.timezone})"

class InvoiceSettings(models.Model):
    prefix = models.CharField(max_length=20, default='INV-')
    logo = models.ImageField(upload_to='invoice_logos/', blank=True, null=True)

    def __str__(self):
        return f"Invoice Settings ({self.prefix})"

class SalarySettings(models.Model):
    # DA and HRA
    da_enabled = models.BooleanField(default=False)
    da_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    hra_enabled = models.BooleanField(default=False)
    hra_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    # Provident Fund
    pf_enabled = models.BooleanField(default=False)
    pf_employee_share = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    pf_org_share = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    # ESI
    esi_enabled = models.BooleanField(default=False)
    esi_employee_share = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    esi_org_share = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    # Gratuity
    gratuity_enabled = models.BooleanField(default=False)
    gratuity_employee_share = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    gratuity_org_share = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    def __str__(self):
        return "Salary Settings"

class ThemeSettings(models.Model):
    LAYOUT_CHOICES = [
        ('vertical', 'Vertical'),
        ('horizontal', 'Horizontal'),
    ]
    LAYOUT_WIDTH_CHOICES = [
        ('fluid', 'Fluid'),
        ('boxed', 'Boxed'),
    ]
    COLOR_SCHEME_CHOICES = [
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('orange', 'Orange'),
        ('blue', 'Blue'),
        ('maroon', 'Maroon'),
        ('purple', 'Purple'),
    ]
    LAYOUT_POSITION_CHOICES = [
        ('scrollable', 'Scrollable'),
        ('fixed', 'Fixed'),
    ]
    TOPBAR_COLOR_CHOICES = [
        ('light', 'Light'),
        ('dark', 'Dark'),
    ]
    SIDEBAR_SIZE_CHOICES = [
        ('default', 'Default'),
        ('small', 'Small'),
        ('large', 'Large'),
    ]
    SIDEBAR_VIEW_CHOICES = [
        ('default', 'Default'),
        ('compact', 'Compact'),
    ]
    SIDEBAR_COLOR_CHOICES = [
        ('light', 'Light'),
        ('dark', 'Dark'),
    ]
    app_name = models.CharField(max_length=100, default='SBS HRM')
    logo_light = models.ImageField(upload_to='theme_logos/', blank=True, null=True)
    logo_dark = models.ImageField(upload_to='theme_logos/', blank=True, null=True)
    favicon = models.ImageField(upload_to='theme_favicons/', blank=True, null=True)
    layout = models.CharField(max_length=20, choices=LAYOUT_CHOICES, default='vertical')
    layout_width = models.CharField(max_length=20, choices=LAYOUT_WIDTH_CHOICES, default='fluid')
    color_scheme = models.CharField(max_length=20, choices=COLOR_SCHEME_CHOICES, default='light')
    layout_position = models.CharField(max_length=20, choices=LAYOUT_POSITION_CHOICES, default='scrollable')
    topbar_color = models.CharField(max_length=20, choices=TOPBAR_COLOR_CHOICES, default='light')
    sidebar_size = models.CharField(max_length=20, choices=SIDEBAR_SIZE_CHOICES, default='default')
    sidebar_view = models.CharField(max_length=20, choices=SIDEBAR_VIEW_CHOICES, default='default')
    sidebar_color = models.CharField(max_length=20, choices=SIDEBAR_COLOR_CHOICES, default='dark')

    def __str__(self):
        return f"Theme Settings ({self.app_name})"

class Tax(models.Model):
    name = models.CharField(max_length=100)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.percentage}%)"

class Expense(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    item_name = models.CharField(max_length=200)
    purchased_from = models.CharField(max_length=200)
    purchased_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_by = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.item_name} - {self.amount}";

class Estimate(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    client = models.ForeignKey('Client', on_delete=models.CASCADE)
    project = models.ForeignKey('Project', on_delete=models.SET_NULL, null=True, blank=True)
    tax = models.ForeignKey('Tax', on_delete=models.SET_NULL, null=True, blank=True)
    client_address = models.TextField(blank=True)
    billing_address = models.TextField(blank=True)
    estimate_date = models.DateField()
    expiry_date = models.DateField()
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    other_info = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Estimate #{self.id} - {self.client.name}"

class EstimateItem(models.Model):
    estimate = models.ForeignKey(Estimate, on_delete=models.CASCADE, related_name='items')
    item = models.CharField(max_length=200)
    description = models.CharField(max_length=300, blank=True)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.item} ({self.estimate})"

class Invoice(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    client = models.ForeignKey('Client', on_delete=models.CASCADE)
    project = models.ForeignKey('Project', on_delete=models.SET_NULL, null=True, blank=True)
    tax = models.ForeignKey('Tax', on_delete=models.SET_NULL, null=True, blank=True)
    client_address = models.TextField(blank=True)
    billing_address = models.TextField(blank=True)
    invoice_date = models.DateField()
    due_date = models.DateField()
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    other_info = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invoice #{self.id} - {self.client.name}"

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    item = models.CharField(max_length=200)
    description = models.CharField(max_length=300, blank=True)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.item} ({self.invoice})"

class EmployeePermission(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    module = models.CharField(max_length=50)
    action = models.CharField(max_length=50)
    allowed = models.BooleanField(default=False)
    locked = models.BooleanField(default=False)

    class Meta:
        unique_together = ('employee', 'module', 'action')

    def __str__(self):
        return f"{self.employee} - {self.module} - {self.action}"
