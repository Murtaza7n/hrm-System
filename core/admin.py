from .models import Department, Employee, Designation, Holiday, Leave, BudgetCategory, Budget, BudgetExpense, BudgetRevenue, Asset
from django.contrib import admin

# Register your models here.

admin.site.register(Department)
admin.site.register(Employee)
# SalarySlip admin removed. PayrollItem and Payslip admin will be added.
admin.site.register(Designation)
admin.site.register(Holiday)
admin.site.register(Leave)
admin.site.register(BudgetCategory)
# No need to reference 'amount' or 'description' for Budget admin registration
admin.site.register(Budget)
admin.site.register(BudgetExpense)
admin.site.register(BudgetRevenue)
admin.site.register(Asset)
