from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Employee, Department, Designation, Attendance, Ticket, Client, Holiday, Leave
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password
from core.models import ChatMessage
from django.db.models import Q, Max
from .models import OnlineUser
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Count
from .models import PayrollItem, Payslip, Employee
from django import forms
from django.db.models import Sum
from .forms import ClientForm, UserAdminForm, ProjectForm
from django.forms import ModelForm
from .models import Project, Department
from .forms import TaskForm
from .models import Task
from django.urls import reverse
from django.http import HttpResponseForbidden

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect('dashboard')
            else:
                return redirect('employee_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'core/login.html')

def is_admin(user):
    return user.is_superuser

def is_employee(user):
    return user.is_authenticated and not user.is_superuser

@user_passes_test(is_admin)
def dashboard(request):
    # Admin dashboard: show all graphs and summary counts
    from django.db.models import Count, Sum
    attendance_stats = Attendance.objects.values('status').annotate(count=Count('id'))
    # Department bar chart: all departments and their employee counts
    dept_counts = Department.objects.annotate(emp_count=Count('employee')).values('name', 'emp_count')
    desig_counts = Designation.objects.annotate(emp_count=Count('employee')).values('name', 'emp_count')
    salary_stats = None
    try:
        salary_stats = Employee.objects.values('department__name').annotate(total_salary=Sum('salary'))
    except Exception:
        pass
    total_employees = Employee.objects.count()
    total_departments = Department.objects.count()
    from .models import Ticket
    total_tickets = Ticket.objects.count()
    total_clients = Client.objects.count()
    return render(request, 'core/dashboard.html', {
        'attendance_stats': list(attendance_stats),
        'dept_counts': list(dept_counts),  # single graph for all departments
        'desig_counts': list(desig_counts),
        'salary_stats': list(salary_stats) if salary_stats else None,
        'total_employees': total_employees,
        'total_departments': total_departments,
        'total_tickets': total_tickets,
        'total_clients': total_clients,
    })

@user_passes_test(is_admin)
def employee_list(request):
    employees = Employee.objects.all()
    departments = Department.objects.all()
    designations = Designation.objects.all()
    return render(request, 'core/employee_list.html', {'employees': employees, 'departments': departments, 'designations': designations})

@user_passes_test(is_admin)
def user_list(request):
    if not request.user.is_authenticated:
        return JsonResponse({'users': []})
    if request.user.is_superuser:
        users = User.objects.exclude(id=request.user.id)
    else:
        users = User.objects.filter(is_superuser=False).exclude(id=request.user.id)
    user_data = [
        {
            'id': u.id,
            'username': u.username,
            'first_name': u.first_name,
            'last_name': u.last_name,
            'initials': (u.first_name[:1] + u.last_name[:1]).upper() if u.first_name or u.last_name else u.username[:2].upper()
        }
        for u in users
    ]
    return JsonResponse({'users': user_data})

@user_passes_test(is_admin)
def add_employee(request):
    departments = Department.objects.all()
    designations = Designation.objects.all()
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        department_id = request.POST.get('department')
        designation_id = request.POST.get('designation')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        if not address:
            address = ''
        date_of_joining = request.POST.get('date_of_joining')
        if not date_of_joining:
            date_of_joining = None
        if User.objects.filter(username=username).exists():
            error = 'Username already exists. Please choose another.'
            return render(request, 'core/add_employee.html', {'departments': departments, 'designations': designations, 'error': error})
        user = User.objects.create(
            username=username,
            password=make_password(password),
            first_name=first_name,
            last_name=last_name,
        )
        employee = Employee.objects.create(
            user=user,
            department_id=department_id,
            designation_id=designation_id,
            phone=phone,
            address=address,
            date_of_joining=date_of_joining,
        )
        return render(request, 'core/employee_created.html', {'username': username, 'password': password})
    return render(request, 'core/add_employee.html', {'departments': departments, 'designations': designations, 'error': error})

class DepartmentForm(ModelForm):
    class Meta:
        model = Department
        fields = ['name']

@user_passes_test(is_admin)
def manage_departments(request):
    departments = Department.objects.all().order_by('name')
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_departments')
    else:
        form = DepartmentForm()
    # For graph: employee count per department
    from django.db.models import Count
    dept_counts = Department.objects.annotate(emp_count=Count('employee')).values('name', 'emp_count')
    return render(request, 'core/manage_departments.html', {'departments': departments, 'form': form, 'dept_counts': list(dept_counts)})

@user_passes_test(is_admin)
def manage_designations(request):
    designations = Designation.objects.all().order_by('name')
    if request.method == 'POST':
        form = DesignationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_designations')
    else:
        form = DesignationForm()
    # For graph: employee count per designation
    from django.db.models import Count
    desig_counts = Designation.objects.annotate(emp_count=Count('employee')).values('name', 'emp_count')
    return render(request, 'core/manage_designations.html', {'designations': designations, 'form': form, 'desig_counts': list(desig_counts)})

class DesignationForm(ModelForm):
    class Meta:
        model = Designation
        fields = ['name', 'description']

@user_passes_test(is_admin)
def delete_department(request, department_id):
    Department.objects.filter(id=department_id).delete()
    return redirect('manage_departments')

@user_passes_test(is_admin)
def delete_designation(request, designation_id):
    Designation.objects.filter(id=designation_id).delete()
    return redirect('manage_designations')

@login_required
def my_department(request):
    try:
        department = request.user.employee.department
    except Exception:
        department = None
    return render(request, 'core/my_department.html', {'department': department})

@login_required
def my_designation(request):
    try:
        designation = request.user.employee.designation
    except Exception:
        designation = None
    return render(request, 'core/my_designation.html', {'designation': designation})

@login_required
def employee_dashboard(request):
    from django.db.models import Count, Sum
    # Attendance stats for graph
    attendance_stats = Attendance.objects.filter(user=request.user).values('status').annotate(count=Count('id'))
    # Department bar chart: all departments and their employee counts
    dept_counts = Department.objects.annotate(emp_count=Count('employee')).values('name', 'emp_count')
    desig_counts = Designation.objects.annotate(emp_count=Count('employee')).values('name', 'emp_count')
    # Salary graph: Payroll and Payslip stats will be added here
    return render(request, 'core/employee_dashboard.html', {
        'attendance_stats': list(attendance_stats),
        'dept_counts': list(dept_counts),
        'desig_counts': list(desig_counts),
        # 'payroll_stats': ...
    })

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def chat_user_list(request):
    user = request.user
    if user.is_superuser:
        users = User.objects.exclude(id=user.id)
    else:
        users = User.objects.filter(is_superuser=False).exclude(id=user.id)
    online_ids = set(OnlineUser.objects.values_list('user_id', flat=True))
    user_data = []
    for u in users:
        last_msg = ChatMessage.objects.filter(
            (Q(sender=user, recipient=u) | Q(sender=u, recipient=user))
        ).order_by('-timestamp').first()
        user_data.append({
            'id': u.id,
            'username': u.username,
            'first_name': u.first_name,
            'last_name': u.last_name,
            'initials': (u.first_name[:1] + u.last_name[:1]).upper() if u.first_name or u.last_name else u.username[:2].upper(),
            'last_message': last_msg.content if last_msg else '',
            'last_timestamp': last_msg.timestamp.strftime('%Y-%m-%d %H:%M') if last_msg else '',
            'online': u.id in online_ids,
        })
    return JsonResponse({'users': user_data})

@login_required
def my_tickets(request):
    tickets = Ticket.objects.filter(created_by=request.user).order_by('-created_at')
    return render(request, 'core/my_tickets.html', {'tickets': tickets})

@login_required
def submit_ticket(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        Ticket.objects.create(title=title, description=description, created_by=request.user)
        return redirect('my_tickets')
    return render(request, 'core/submit_ticket.html')

@user_passes_test(is_admin)
def all_tickets(request):
    tickets = Ticket.objects.all().order_by('-created_at')
    return render(request, 'core/all_tickets.html', {'tickets': tickets})

@user_passes_test(is_admin)
def update_ticket_status(request, ticket_id):
    ticket = Ticket.objects.get(id=ticket_id)
    if request.method == 'POST':
        ticket.status = request.POST.get('status')
        ticket.save()
        return redirect('all_tickets')
    return render(request, 'core/update_ticket.html', {'ticket': ticket})

@login_required
def delete_ticket(request, ticket_id):
    ticket = Ticket.objects.get(id=ticket_id)
    if request.user.is_superuser or ticket.created_by == request.user:
        ticket.delete()
        if request.user.is_superuser:
            return redirect('all_tickets')
        else:
            return redirect('my_tickets')
    else:
        messages.error(request, 'You do not have permission to delete this ticket.')
        if request.user.is_superuser:
            return redirect('all_tickets')
        else:
            return redirect('my_tickets')

@login_required
def my_attendance(request):
    today = timezone.now().date()
    records = Attendance.objects.filter(user=request.user).order_by('-date')
    today_record = records.filter(date=today).first()
    # Remove can_view_attendance permission check
    if request.method == 'POST':
        if not today_record:
            check_in = timezone.now().time()
            Attendance.objects.create(user=request.user, date=today, check_in=check_in, status='present')
        elif today_record and not today_record.check_out:
            today_record.check_out = timezone.now().time()
            today_record.save()
        return redirect('my_attendance')
    return render(request, 'core/my_attendance.html', {'records': records, 'today_record': today_record})

@user_passes_test(is_admin)
def all_attendance(request):
    from datetime import datetime
    users = User.objects.filter(is_superuser=False)
    user_id = request.GET.get('user_id')
    month = request.GET.get('month')
    year = request.GET.get('year')
    records = Attendance.objects.select_related('user').order_by('-date')
    if user_id:
        records = records.filter(user_id=user_id)
    if month and year:
        records = records.filter(date__month=month, date__year=year)
    # Prepare hours worked per day for the graph
    from collections import OrderedDict
    import calendar
    hours_per_day = OrderedDict()
    has_hours_data = False
    if user_id and month and year:
        days_in_month = calendar.monthrange(int(year), int(month))[1]
        for day in range(1, days_in_month+1):
            hours_per_day[day] = 0
        for rec in records:
            if rec.check_in and rec.check_out and rec.date.month == int(month) and rec.date.year == int(year):
                delta = datetime.combine(rec.date, rec.check_out) - datetime.combine(rec.date, rec.check_in)
                hours = round(delta.total_seconds() / 3600, 2)
                hours_per_day[rec.date.day] = hours
        has_hours_data = any(v > 0 for v in hours_per_day.values())
    else:
        hours_per_day = None
    # For graph: attendance count by status
    status_counts = Attendance.objects.values('status').annotate(count=Count('id'))
    return render(request, 'core/all_attendance.html', {
        'records': records,
        'status_counts': list(status_counts),
        'users': users,
        'selected_user_id': user_id,
        'selected_month': month,
        'selected_year': year,
        'hours_per_day': hours_per_day,
        'has_hours_data': has_hours_data,
    })

class HolidayForm(ModelForm):
    class Meta:
        model = Holiday
        fields = ['name', 'date', 'description']

@user_passes_test(is_admin)
def manage_holidays(request):
    holidays = Holiday.objects.all()
    if request.method == 'POST':
        form = HolidayForm(request.POST)
        if form.is_valid():
            holiday = form.save(commit=False)
            holiday.created_by = request.user
            holiday.save()
            return redirect('manage_holidays')
    else:
        form = HolidayForm()
    return render(request, 'core/manage_holidays.html', {'holidays': holidays, 'form': form})

@user_passes_test(is_admin)
def delete_holiday(request, holiday_id):
    Holiday.objects.filter(id=holiday_id).delete()
    return redirect('manage_holidays')

@login_required
def holidays(request):
    holidays = Holiday.objects.all()
    return render(request, 'core/holidays.html', {'holidays': holidays})

class LeaveForm(ModelForm):
    class Meta:
        model = Leave
        fields = ['start_date', 'end_date', 'leave_type', 'reason']

@login_required
def apply_leave(request):
    try:
        employee = request.user.employee
    except Employee.DoesNotExist:
        return render(request, 'core/no_employee.html')
    if request.method == 'POST':
        form = LeaveForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.employee = employee
            leave.save()
            return redirect('my_leaves')
    else:
        form = LeaveForm()
    return render(request, 'core/apply_leave.html', {'form': form})

@login_required
def my_leaves(request):
    try:
        employee = request.user.employee
    except Employee.DoesNotExist:
        return render(request, 'core/no_employee.html')
    leaves = Leave.objects.filter(employee=employee).order_by('-applied_at')
    return render(request, 'core/my_leaves.html', {'leaves': leaves})

@user_passes_test(is_admin)
def manage_leaves(request):
    leaves = Leave.objects.select_related('employee__user').order_by('-applied_at')
    if request.method == 'POST':
        leave_id = request.POST.get('leave_id')
        action = request.POST.get('action')
        comments = request.POST.get('comments', '')
        leave = Leave.objects.get(id=leave_id)
        leave.status = action
        leave.reviewed_by = request.user
        leave.reviewed_at = timezone.now()
        leave.comments = comments
        leave.save()
        return redirect('manage_leaves')
    return render(request, 'core/manage_leaves.html', {'leaves': leaves})

@user_passes_test(is_admin)
def edit_employee(request, employee_id):
    employee = Employee.objects.select_related('user').get(id=employee_id)
    departments = Department.objects.all()
    designations = Designation.objects.all()
    error = None
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        department_id = request.POST.get('department')
        designation_id = request.POST.get('designation')
        date_of_joining = request.POST.get('date_of_joining')
        if not date_of_joining:
            date_of_joining = None
        employee.user.first_name = first_name
        employee.user.last_name = last_name
        employee.user.save()
        employee.phone = phone
        employee.address = address
        employee.department_id = department_id
        employee.designation_id = designation_id
        employee.date_of_joining = date_of_joining
        employee.save()
        return redirect('employee_list')
    return render(request, 'core/edit_employee.html', {
        'employee': employee,
        'departments': departments,
        'designations': designations,
        'error': error
    })

@user_passes_test(is_admin)
def delete_employee(request, employee_id):
    employee = Employee.objects.select_related('user').get(id=employee_id)
    user = employee.user
    if user == request.user:
        messages.warning(request, 'You cannot delete your own account while logged in.')
        return redirect('employee_list')
    employee.delete()
    user.delete()
    return redirect('employee_list')

@require_POST
@user_passes_test(is_admin)
def change_employee_role(request, employee_id):
    employee = Employee.objects.get(id=employee_id)
    role_id = request.POST.get('role_id')
    employee.role_id = role_id if role_id else None
    employee.save()
    return redirect('employee_list')

# Remove all permission matrix and old permission logic

@user_passes_test(is_admin)
def admin_roles(request):
    roles = Role.objects.all()
    # For each role, get a summary of permissions
    role_permissions = {}
    for role in roles:
        perms = Permission.objects.filter(role=role)
        if perms.exists():
            perm_summary = ', '.join(sorted(set([f"{p.module}:{p.action}" for p in perms if p.allowed])))
        else:
            perm_summary = 'No permissions'
        role_permissions[role.id] = perm_summary
    return render(request, 'core/admin_roles.html', {
        'roles': roles,
        'role_permissions': role_permissions,
    })

@user_passes_test(is_admin)
def client_list(request):
    clients = Client.objects.all()
    return render(request, 'core/client_list.html', {'clients': clients})

@user_passes_test(is_admin)
def add_client(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('client_list')
    else:
        form = ClientForm()
    return render(request, 'core/add_client.html', {'form': form})

@user_passes_test(is_admin)
def edit_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            return redirect('client_list')
    else:
        form = ClientForm(instance=client)
    return render(request, 'core/edit_client.html', {'form': form, 'client': client})

@user_passes_test(is_admin)
def delete_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    if request.method == 'POST':
        client.delete()
        return redirect('client_list')
    return render(request, 'core/delete_client.html', {'client': client})

@user_passes_test(is_admin)
def project_list(request):
    projects = Project.objects.select_related('client', 'manager__department', 'manager__designation').all()
    return render(request, 'core/project_list.html', {'projects': projects})

@user_passes_test(is_admin)
def add_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('project_list')
    else:
        form = ProjectForm()
    return render(request, 'core/add_project.html', {'form': form})

@user_passes_test(is_admin)
def edit_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect('project_list')
    else:
        form = ProjectForm(instance=project)
    return render(request, 'core/edit_project.html', {'form': form, 'project': project})

@user_passes_test(is_admin)
def delete_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    project.delete()
    return redirect('project_list')

@login_required
def assign_task(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    # Only project manager or admin can assign tasks
    if not (request.user.is_superuser or (project.manager and project.manager.user == request.user)):
        return HttpResponseForbidden('You do not have permission to assign tasks for this project.')
    manager = project.manager if project.manager else None
    if request.method == 'POST':
        form = TaskForm(request.POST, project=project, manager=manager)
        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.assigned_by = manager if manager else None
            task.save()
            return redirect(reverse('project_tasks', args=[project.id]))
    else:
        form = TaskForm(project=project, manager=manager)
    return render(request, 'core/assign_task.html', {'form': form, 'project': project})

@login_required
def project_tasks(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    # Only project manager or admin can view all tasks
    if not (request.user.is_superuser or (project.manager and project.manager.user == request.user)):
        return HttpResponseForbidden('You do not have permission to view tasks for this project.')
    tasks = Task.objects.filter(project=project).select_related('assigned_to')
    return render(request, 'core/project_tasks.html', {'project': project, 'tasks': tasks})

@login_required
def my_tasks(request):
    try:
        employee = request.user.employee
    except Employee.DoesNotExist:
        return render(request, 'core/no_employee.html')
    tasks = Task.objects.filter(assigned_to=employee).select_related('project', 'assigned_by')
    return render(request, 'core/my_tasks.html', {'tasks': tasks})

@login_required
def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    # Only project manager or admin can assign tasks
    can_assign = request.user.is_superuser or (project.manager and project.manager.user == request.user)
    departments = Department.objects.prefetch_related('employee_set__designation').all()
    employees_by_dept = []
    for dept in departments:
        emps = dept.employee_set.select_related('user', 'designation').all()
        employees_by_dept.append((dept, emps))
    if request.method == 'POST' and can_assign:
        selected_employee_ids = request.POST.getlist('assigned_to')
        form = TaskForm(request.POST, request.FILES)
        if form.is_valid() and selected_employee_ids:
            for emp_id in selected_employee_ids:
                emp = Employee.objects.get(id=emp_id)
                task = form.save(commit=False)
                task.project = project
                task.assigned_by = project.manager if project.manager else None
                task.assigned_to = emp
                task.save()
            return redirect('project_detail', project_id=project.id)
    else:
        form = TaskForm()
    return render(request, 'core/project_detail.html', {
        'project': project,
        'can_assign': can_assign,
        'departments': departments,
        'employees_by_dept': employees_by_dept,
        'form': form,
    })

@login_required
def select_project_for_task(request):
    if request.user.is_superuser:
        projects = Project.objects.all()
    elif hasattr(request.user, 'employee') and request.user.employee.designation and request.user.employee.designation.name == 'Project Manager':
        projects = Project.objects.filter(manager=request.user.employee)
    else:
        projects = Project.objects.none()
    if request.method == 'POST':
        project_id = request.POST.get('project_id')
        if project_id:
            return redirect('assign_task', project_id=project_id)
    return render(request, 'core/select_project_for_task.html', {'projects': projects})

@login_required
def select_project_for_view_tasks(request):
    if request.user.is_superuser:
        projects = Project.objects.all()
    elif hasattr(request.user, 'employee') and request.user.employee.designation and request.user.employee.designation.name == 'Project Manager':
        projects = Project.objects.filter(manager=request.user.employee)
    else:
        projects = Project.objects.none()
    if request.method == 'POST':
        project_id = request.POST.get('project_id')
        if project_id:
            return redirect('project_tasks', project_id=project_id)
    return render(request, 'core/select_project_for_view_tasks.html', {'projects': projects})

@login_required
def edit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if request.method == 'POST':
        form = TaskForm(request.POST, request.FILES, instance=task)
        if form.is_valid():
            form.save()
            return redirect('project_tasks', project_id=task.project.id)
    else:
        form = TaskForm(instance=task)
    return render(request, 'core/edit_task.html', {'form': form, 'task': task})

@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    project_id = task.project.id
    if request.method == 'POST':
        task.delete()
        return redirect('project_tasks', project_id=project_id)
    return render(request, 'core/delete_task.html', {'task': task})
