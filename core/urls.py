from . import views
from django.urls import path

urlpatterns = [
    path('employees/', views.employee_list, name='employee_list'),
    path('projects/<int:project_id>/assign-task/', views.assign_task, name='assign_task'),
    path('projects/<int:project_id>/tasks/', views.project_tasks, name='project_tasks'),
    path('my-tasks/', views.my_tasks, name='my_tasks'),
    path('projects/<int:project_id>/', views.project_detail, name='project_detail'),
    path('select-project-for-task/', views.select_project_for_task, name='select_project_for_task'),
    path('select-project-for-view-tasks/', views.select_project_for_view_tasks, name='select_project_for_view_tasks'),
    path('tasks/<int:task_id>/edit/', views.edit_task, name='edit_task'),
    path('tasks/<int:task_id>/delete/', views.delete_task, name='delete_task'),
] 