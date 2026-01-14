from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import *

urlpatterns = [
    path('login/', LoginView.as_view()),
    path('leave/apply/', ApplyLeaveView.as_view()),
    path('leave/approve/<int:leave_id>/', ApproveLeaveView.as_view()),
    
    
    path('export/leaves/', ExportLeavesView.as_view()),
    path(
        'create-employee/',
        CreateEmployeeView.as_view(),
        name='create_employee'
    ),
    path(
        'create-manager/',
        CreateManagerView.as_view(),
        name='create_manager'
    ),
    path(
        'leave-history/',
        EmployeeLeaveHistoryView.as_view(),
        name='employee_leave_history'
    ),

    path(
        'manager/leaves/',
        ManagerPendingLeavesView.as_view(),
        name='manager_pending_leaves'
    ),
    path(
        'dashboard/manager/',
        ManagerDashboardLeavesView.as_view(),
        name='manager_dashboard_leaves'
    ),

    path(
        'admin_dashboard/',
        AdminDashboardLeavesView.as_view(),
        name='admin_dashboard_leaves'
    ),

    path(
        'leave/edit/<int:leave_id>/',
        EditPendingLeaveView.as_view(),
        name='edit_pending_leave'
    ),

    path(
        'leave/cancel/<int:leave_id>/',
        CancelPendingLeaveView.as_view(),
        name='cancel_pending_leave'
    ),

    path(
        'employee/profile/upload-image/',
        UploadProfileImageView.as_view(),
        name='upload_profile_image'
    ),
    path(
        'employee/profile/view-image/',
        ViewProfileImageView.as_view(),
        name='view_profile_image'
    ),
    path(
    'profile/',
    ProfileManagementView.as_view(),
    name='profile_management'
),

path(
    'sick-document/<int:leave_id>/',
    ManagerViewSickLeaveDocumentView.as_view(),
    name='manager_view_sick_leave_document'
),

]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
