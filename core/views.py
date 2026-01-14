from django.views import View
from django.http import JsonResponse, FileResponse, JsonResponse
from .models import User, Leave, LeaveDocument
from .auth import generate_tokens
import openpyxl
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from core.permissions import is_admin
import json
from core.models import User, Role, Leave, LeaveDocument
from core.permissions import is_employee, is_manager
from core.utils.email_service import send_leave_status_email
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(View):
    def post(self, request):
        user = User.objects.get(email=request.POST['email'])
        if not user.check_password(request.POST['password']):
            return JsonResponse({'error': 'Invalid credentials'}, status=401)
        return JsonResponse(generate_tokens(user))

@method_decorator(csrf_exempt, name='dispatch')
class CreateEmployeeView(View):
    def post(self, request):

        # 🔐 Authentication check
        if request.user.is_anonymous:
            return JsonResponse(
                {'error': 'Authentication required'},
                status=401
            )

        # 🔐 Authorization check (ADMIN ONLY)
        if not is_admin(request.user):
            return JsonResponse(
                {'error': 'Permission denied. Admin access only.'},
                status=403
            )

        # 📥 Parse JSON body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        email = data.get('email')
        password = data.get('password')
        name = data.get('name')

        # 🔁 NOW THIS IS MANAGER'S EMPLOYEE_ID (e.g. "MGR001")
        manager_employee_id = data.get('manager_id')

        employee_business_id = data.get('employee_id')

        if not all([email, password, name, manager_employee_id, employee_business_id]):
            return JsonResponse(
                {
                    'error': 'email, password, name, employee_id, and manager_id are required'
                },
                status=400
            )

        # 🔍 Fetch EMPLOYEE role
        try:
            employee_role = Role.objects.get(role_name='EMPLOYEE')
        except Role.DoesNotExist:
            return JsonResponse({'error': 'EMPLOYEE role not found'}, status=500)

        # 🔍 Fetch manager USING employee_id (NOT PK)
        try:
            manager = User.objects.get(employee_id=manager_employee_id)
        except User.DoesNotExist:
            return JsonResponse(
                {'error': 'Manager with given employee_id not found'},
                status=404
            )

        # 🔐 Validate manager role
        if manager.role.role_name != 'MANAGER':
            return JsonResponse(
                {'error': 'Assigned user is not a manager'},
                status=400
            )

        # 🚫 Prevent duplicate email
        if User.objects.filter(email=email).exists():
            return JsonResponse(
                {'error': 'User with this email already exists'},
                status=400
            )

        # 🚫 Prevent duplicate employee_id
        if User.objects.filter(employee_id=employee_business_id).exists():
            return JsonResponse(
                {'error': 'Employee ID already exists'},
                status=400
            )

        # ✅ Create employee
        employee = User.objects.create_user(
            email=email,
            password=password,
            name=name,
            role=employee_role,
            manager=manager
        )

        employee.employee_id = employee_business_id
        employee.save()

        return JsonResponse(
            {
                'message': 'Employee created and assigned to manager successfully',
                'employee_db_id': employee.id,
                'employee_id': employee.employee_id,
                'manager_employee_id': manager.employee_id
            },
            status=201
        )

@method_decorator(csrf_exempt, name='dispatch')
class CreateManagerView(View):
    def post(self, request):

        # 🔐 Authentication check
        if request.user.is_anonymous:
            return JsonResponse(
                {'error': 'Authentication required'},
                status=401
            )

        # 🔐 Authorization check (ADMIN ONLY)
        if not is_admin(request.user):
            return JsonResponse(
                {'error': 'Permission denied. Admin access only.'},
                status=403
            )

        # 📥 Parse JSON body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        email = data.get('email')
        password = data.get('password')
        name = data.get('name')
        employee_id = data.get('employee_id')  # optional business ID

        if not all([email, password, name]):
            return JsonResponse(
                {'error': 'email, password, and name are required'},
                status=400
            )

        # 🚫 Prevent duplicate email
        if User.objects.filter(email=email).exists():
            return JsonResponse(
                {'error': 'User with this email already exists'},
                status=400
            )

        # 🚫 Prevent duplicate employee_id (if provided)
        if employee_id and User.objects.filter(employee_id=employee_id).exists():
            return JsonResponse(
                {'error': 'Employee ID already exists'},
                status=400
            )

        # 🔍 Get MANAGER role
        try:
            manager_role = Role.objects.get(role_name='MANAGER')
        except Role.DoesNotExist:
            return JsonResponse(
                {'error': 'MANAGER role not found'},
                status=500
            )

        # ✅ Create manager (NO manager assignment)
        manager = User.objects.create_user(
            email=email,
            password=password,
            name=name,
            role=manager_role
        )

        # Optional business employee_id
        if employee_id:
            manager.employee_id = employee_id
            manager.save()

        return JsonResponse({
            'message': 'Manager created successfully',
            'manager_id': manager.id
        }, status=201)

from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from core.models import Leave, LeaveDocument


@method_decorator(csrf_exempt, name='dispatch')
class ApplyLeaveView(View):
    def post(self, request):

        # 🔐 Authentication check
        if request.user.is_anonymous:
            return JsonResponse(
                {'error': 'Authentication required'},
                status=401
            )

        leave_type = request.POST.get('leave_type')

        # 📎 Sick leave document validation
        if leave_type == 'SICK':
            if 'document' not in request.FILES:
                return JsonResponse(
                    {'error': 'Document is required for sick leave'},
                    status=400
                )

            document = request.FILES['document']

            # 🔒 File size validation (2 MB)
            MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB
            if document.size > MAX_FILE_SIZE:
                return JsonResponse(
                    {
                        'error': 'Uploaded document is too large',
                        'max_size': '2 MB'
                    },
                    status=400
                )

        # 📄 Create leave
        leave = Leave.objects.create(
            user=request.user,
            leave_type=leave_type,
            start_date=request.POST.get('start_date'),
            end_date=request.POST.get('end_date'),
            reason=request.POST.get('reason')
        )

        # 📎 Save document if present
        if 'document' in request.FILES:
            LeaveDocument.objects.create(
                leave=leave,
                file=request.FILES['document']
            )

        return JsonResponse(
            {'message': 'Leave applied successfully'},
            status=201
        )

@method_decorator(csrf_exempt, name='dispatch')
class ApproveLeaveView(View):
    def post(self, request, leave_id):
        leave = Leave.objects.get(id=leave_id)

        if leave.user == request.user:
            return JsonResponse({'error': 'Cannot approve own leave'}, status=403)

        leave.status = request.POST['status']
        leave.approved_by = request.user
        leave.save()
        return JsonResponse({'message': 'Leave updated'})


@method_decorator(csrf_exempt, name='dispatch')
class EmployeeLeaveHistoryView(View):
    def get(self, request):

        # 🔐 Authentication check
        if request.user.is_anonymous:
            return JsonResponse(
                {'error': 'Authentication required'},
                status=401
            )

        # 🔐 Authorization check (EMPLOYEE ONLY)
        if not is_employee(request.user):
            return JsonResponse(
                {'error': 'Permission denied. Employee access only.'},
                status=403
            )

        # 📄 Fetch leave history for logged-in employee
        leaves = Leave.objects.filter(user=request.user).order_by('-start_date')

        leave_data = []
        for leave in leaves:
            leave_data.append({
                'leave_id': leave.id,
                'leave_type': leave.leave_type,
                'start_date': leave.start_date,
                'end_date': leave.end_date,
                'reason': leave.reason,
                'status': leave.status,
                'approved_by': (
                    leave.approved_by.employee_id
                    if leave.approved_by else None
                )
            })

        return JsonResponse({
            'employee_id': request.user.employee_id,
            'total_leaves': len(leave_data),
            'leave_history': leave_data
        }, status=200)

@method_decorator(csrf_exempt, name='dispatch')
class ManagerPendingLeavesView(View):
    def get(self, request):

        # 🔐 Authentication check
        if request.user.is_anonymous:
            return JsonResponse(
                {'error': 'Authentication required'},
                status=401
            )

        # 🔐 Authorization check (MANAGER ONLY)
        if not is_manager(request.user):
            return JsonResponse(
                {'error': 'Permission denied. Manager access only.'},
                status=403
            )

        # 📄 Fetch pending leaves of employees under this manager
        leaves = Leave.objects.filter(
            user__manager=request.user,
            status='PENDING'
        ).select_related('user').order_by('start_date')

        pending_leaves = []
        for leave in leaves:
            pending_leaves.append({
                'leave_id': leave.id,
                'employee_id': leave.user.employee_id,
                'employee_name': leave.user.name,
                'leave_type': leave.leave_type,
                'start_date': leave.start_date,
                'end_date': leave.end_date,
                'reason': leave.reason,
                'status': leave.status
            })

        return JsonResponse({
            'manager_id': request.user.employee_id,
            'total_pending_leaves': len(pending_leaves),
            'pending_leaves': pending_leaves
        }, status=200)

@method_decorator(csrf_exempt, name='dispatch')
class ManagerDashboardLeavesView(View):
    def get(self, request):

        # 🔐 Authentication check
        if request.user.is_anonymous:
            return JsonResponse(
                {'error': 'Authentication required'},
                status=401
            )

        # 🔐 Authorization check (MANAGER ONLY)
        if not is_manager(request.user):
            return JsonResponse(
                {'error': 'Permission denied. Manager access only.'},
                status=403
            )

        # 📄 Fetch ALL leaves of employees under this manager
        leaves = (
            Leave.objects
            .filter(user__manager=request.user)
            .select_related('user', 'approved_by')
            .order_by('-created_at')
        )

        dashboard_data = []
        summary = {
            'PENDING': 0,
            'APPROVED': 0,
            'REJECTED': 0
        }

        for leave in leaves:
            summary[leave.status] += 1

            dashboard_data.append({
                'leave_id': leave.id,
                'employee_id': leave.user.employee_id,
                'employee_name': leave.user.name,
                'employee_email': leave.user.email,
                'leave_type': leave.leave_type,
                'start_date': leave.start_date,
                'end_date': leave.end_date,
                'reason': leave.reason,
                'status': leave.status,
                'approved_by': (
                    leave.approved_by.employee_id
                    if leave.approved_by else None
                ),
                'created_at': leave.created_at
            })

        return JsonResponse({
            'manager_employee_id': request.user.employee_id,
            'total_leaves': len(dashboard_data),
            'summary': summary,
            'leaves': dashboard_data
        }, status=200)

@method_decorator(csrf_exempt, name='dispatch')
class AdminDashboardLeavesView(View):
    def get(self, request):

        # 🔐 Authentication check
        if request.user.is_anonymous:
            return JsonResponse(
                {'error': 'Authentication required'},
                status=401
            )

        # 🔐 Authorization check (ADMIN ONLY)
        if not is_admin(request.user):
            return JsonResponse(
                {'error': 'Permission denied. Admin access only.'},
                status=403
            )

        # 📄 Fetch all managers
        managers = User.objects.filter(role__role_name='MANAGER')

        dashboard_data = []
        overall_summary = {
            'PENDING': 0,
            'APPROVED': 0,
            'REJECTED': 0
        }

        for manager in managers:
            leaves = (
                Leave.objects
                .filter(user__manager=manager)
                .select_related('user', 'approved_by')
                .order_by('-created_at')
            )

            manager_summary = {
                'PENDING': 0,
                'APPROVED': 0,
                'REJECTED': 0
            }

            leave_list = []

            for leave in leaves:
                manager_summary[leave.status] += 1
                overall_summary[leave.status] += 1

                leave_list.append({
                    'leave_id': leave.id,
                    'employee_id': leave.user.employee_id,
                    'employee_name': leave.user.name,
                    'employee_email': leave.user.email,
                    'leave_type': leave.leave_type,
                    'start_date': leave.start_date,
                    'end_date': leave.end_date,
                    'reason': leave.reason,
                    'status': leave.status,
                    'approved_by': (
                        leave.approved_by.employee_id
                        if leave.approved_by else None
                    ),
                    'created_at': leave.created_at
                })

            dashboard_data.append({
                'manager_employee_id': manager.employee_id,
                'manager_name': manager.name,
                'manager_email': manager.email,
                'summary': manager_summary,
                'total_leaves': len(leave_list),
                'leaves': leave_list
            })

        return JsonResponse({
            'overall_summary': overall_summary,
            'managers': dashboard_data
        }, status=200)

@method_decorator(csrf_exempt, name='dispatch')
class EditPendingLeaveView(View):
    def put(self, request, leave_id):

        # 🔐 Authentication check
        if request.user.is_anonymous:
            return JsonResponse(
                {'error': 'Authentication required'},
                status=401
            )

        # 🔐 Authorization check (EMPLOYEE ONLY)
        if not is_employee(request.user):
            return JsonResponse(
                {'error': 'Permission denied. Employee access only.'},
                status=403
            )

        # 🔍 Fetch leave
        try:
            leave = Leave.objects.get(id=leave_id, is_active=True)
        except Leave.DoesNotExist:
            return JsonResponse(
                {'error': 'Leave not found'},
                status=404
            )

        # 🔐 Ownership check
        if leave.user != request.user:
            return JsonResponse(
                {'error': 'You are not allowed to edit this leave'},
                status=403
            )

        # 🚫 Status check
        if leave.status != 'PENDING':
            return JsonResponse(
                {
                    'error': 'Only pending leave can be edited',
                    'current_status': leave.status
                },
                status=400
            )

        # 📥 Parse request body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        # ✏️ Editable fields
        leave_type = data.get('leave_type')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        reason = data.get('reason')

        if not any([leave_type, start_date, end_date, reason]):
            return JsonResponse(
                {'error': 'At least one field must be provided for update'},
                status=400
            )

        # ✅ Apply updates
        if leave_type:
            leave.leave_type = leave_type
        if start_date:
            leave.start_date = start_date
        if end_date:
            leave.end_date = end_date
        if reason:
            leave.reason = reason

        leave.save()  # updated_at auto-updates

        return JsonResponse(
            {
                'message': 'Leave updated successfully',
                'leave_id': leave.id,
                'status': leave.status
            },
            status=200
        )
@method_decorator(csrf_exempt, name='dispatch')
class CancelPendingLeaveView(View):
    def post(self, request, leave_id):

        # 🔐 Authentication check
        if request.user.is_anonymous:
            return JsonResponse(
                {'error': 'Authentication required'},
                status=401
            )

        # 🔐 Authorization check (EMPLOYEE ONLY)
        if not is_employee(request.user):
            return JsonResponse(
                {'error': 'Permission denied. Employee access only.'},
                status=403
            )

        # 🔍 Fetch active leave
        try:
            leave = Leave.objects.get(id=leave_id, is_active=True)
        except Leave.DoesNotExist:
            return JsonResponse(
                {'error': 'Leave not found or already cancelled'},
                status=404
            )

        # 🔐 Ownership check
        if leave.user != request.user:
            return JsonResponse(
                {'error': 'You are not allowed to cancel this leave'},
                status=403
            )

        # 🚫 Status check
        if leave.status == 'APPROVED':
            return JsonResponse(
                {'error': 'Approved leave cannot be cancelled'},
                status=400
            )

        if leave.status == 'REJECTED':
            return JsonResponse(
                {'error': 'Rejected leave cannot be cancelled'},
                status=400
            )

        if leave.status != 'PENDING':
            return JsonResponse(
                {'error': 'Only pending leave can be cancelled'},
                status=400
            )

        # ✅ Soft cancel leave
        leave.is_active = False
        leave.save()  # updated_at auto-updates

        return JsonResponse(
            {
                'message': 'Leave cancelled successfully',
                'leave_id': leave.id
            },
            status=200
        )

@method_decorator(csrf_exempt, name='dispatch')
class UploadProfileImageView(View):
    def post(self, request):

        # 🔐 Authentication check
        if request.user.is_anonymous:
            return JsonResponse(
                {'error': 'Authentication required'},
                status=401
            )

        # 🔐 Authorization check (EMPLOYEE ONLY)
        if not is_employee(request.user):
            return JsonResponse(
                {'error': 'Permission denied. Employee access only.'},
                status=403
            )

        # 📷 Check file
        image = request.FILES.get('profile_image')
        if not image:
            return JsonResponse(
                {'error': 'Profile image file is required'},
                status=400
            )

        # Optional: validate file type
        allowed_types = ['image/jpeg', 'image/png']
        if image.content_type not in allowed_types:
            return JsonResponse(
                {'error': 'Only JPG and PNG images are allowed'},
                status=400
            )

        # Optional: validate size (2MB)
        if image.size > 2 * 1024 * 1024:
            return JsonResponse(
                {'error': 'Image size must be less than 2MB'},
                status=400
            )

        # ✅ Save image
        request.user.profile_image = image
        request.user.save()

        return JsonResponse(
            {
                'message': 'Profile image uploaded successfully'
            },
            status=200
        )

class ViewProfileImageView(View):
    def get(self, request):

        # 🔐 Authentication check
        if request.user.is_anonymous:
            return JsonResponse(
                {'error': 'Authentication required'},
                status=401
            )

        # 🔐 Authorization check (EMPLOYEE ONLY)
        if not is_employee(request.user):
            return JsonResponse(
                {'error': 'Permission denied. Employee access only.'},
                status=403
            )

        if not request.user.profile_image:
            return JsonResponse(
                {'error': 'No profile image uploaded'},
                status=404
            )

        return JsonResponse(
            {
                'employee_id': request.user.employee_id,
                'profile_image_url': request.user.profile_image.url
            },
            status=200
        )

@method_decorator(csrf_exempt, name='dispatch')
class ProfileManagementView(View):

    # ---------------- VIEW PROFILE ----------------
    def get(self, request):

        # 🔐 Authentication check
        if request.user.is_anonymous:
            return JsonResponse(
                {'error': 'Authentication required'},
                status=401
            )

        user = request.user

        return JsonResponse(
            {
                'employee_id': user.employee_id,
                'name': user.name,
                'email': user.email,
                'role': user.role.role_name,
                'manager_employee_id': (
                    user.manager.employee_id if user.manager else None
                ),
                'profile_image_url': (
                    user.profile_image.url if user.profile_image else None
                ),
                'is_active': user.is_active
            },
            status=200
        )

    # ---------------- UPDATE PROFILE ----------------
    def put(self, request):

        # 🔐 Authentication check
        if request.user.is_anonymous:
            return JsonResponse(
                {'error': 'Authentication required'},
                status=401
            )

        user = request.user

        # 📥 Parse JSON body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {'error': 'Invalid JSON'},
                status=400
            )

        # ✏️ Allowed fields
        allowed_fields = ['name']

        # 🚫 Check for forbidden fields
        for field in data.keys():
            if field not in allowed_fields:
                return JsonResponse(
                    {'error': f'Field "{field}" cannot be updated'},
                    status=400
                )

        # 🚫 Empty update
        if not data:
            return JsonResponse(
                {'error': 'No data provided for update'},
                status=400
            )

        # ✅ Update allowed fields
        if 'name' in data:
            user.name = data['name']

        user.save()

        return JsonResponse(
            {
                'message': 'Profile updated successfully',
                'name': user.name
            },
            status=200
        )


@method_decorator(csrf_exempt, name='dispatch')
class ApproveLeaveView(View):
    def post(self, request, leave_id):

        # 🔐 Authentication
        if request.user.is_anonymous:
            return JsonResponse({'error': 'Authentication required'}, status=401)

        # 🔐 Authorization
        if not is_manager(request.user):
            return JsonResponse({'error': 'Manager access only'}, status=403)

        try:
            leave = Leave.objects.get(id=leave_id, is_active=True)
        except Leave.DoesNotExist:
            return JsonResponse({'error': 'Leave not found'}, status=404)

        # 🔐 Ensure employee belongs to manager
        if leave.user.manager != request.user:
            return JsonResponse({'error': 'Not authorized for this leave'}, status=403)

        if leave.status != 'PENDING':
            return JsonResponse(
                {'error': f'Leave already {leave.status.lower()}'},
                status=400
            )

        action = request.POST.get('action')  # APPROVED / REJECTED

        if action not in ['APPROVED', 'REJECTED']:
            return JsonResponse(
                {'error': 'Invalid action. Use APPROVED or REJECTED'},
                status=400
            )

        # ✅ Update leave
        leave.status = action
        leave.approved_by = request.user
        leave.save()

        # 📧 Send email notification
        send_leave_status_email(leave, action)

        return JsonResponse(
            {
                'message': f'Leave {action.lower()} successfully',
                'leave_id': leave.id,
                'status': leave.status
            },
            status=200
        )

@method_decorator(csrf_exempt, name='dispatch')
class ManagerViewSickLeaveDocumentView(View):
    def get(self, request, leave_id):

        # 🔐 Authentication check
        if request.user.is_anonymous:
            return JsonResponse(
                {'error': 'Authentication required'},
                status=401
            )

        # 🔐 Authorization check (MANAGER ONLY)
        if not is_manager(request.user):
            return JsonResponse(
                {'error': 'Permission denied. Manager access only.'},
                status=403
            )

        # 🔍 Fetch leave
        try:
            leave = Leave.objects.get(id=leave_id, is_active=True)
        except Leave.DoesNotExist:
            return JsonResponse(
                {'error': 'Leave not found'},
                status=404
            )

        # 🔐 Ensure leave belongs to manager’s employee
        if leave.user.manager != request.user:
            return JsonResponse(
                {'error': 'You are not authorized to view this document'},
                status=403
            )

        # 🩺 Ensure sick leave
        if leave.leave_type != 'SICK':
            return JsonResponse(
                {'error': 'This leave is not a sick leave'},
                status=400
            )

        # 📄 Fetch document
        try:
            document = leave.documents.first()
        except LeaveDocument.DoesNotExist:
            return JsonResponse(
                {'error': 'No document uploaded for this sick leave'},
                status=404
            )

        if not document:
            return JsonResponse(
                {'error': 'No document uploaded for this sick leave'},
                status=404
            )

        # 📎 Return file securely
        return FileResponse(
            document.file.open('rb'),
            as_attachment=True,
            filename=document.file.name.split('/')[-1]
        )

@method_decorator(csrf_exempt, name='dispatch')
class ExportLeavesView(View):
    def get(self, request):

        # 🔐 Authentication & Authorization (ADMIN ONLY)
        if request.user.is_anonymous or not is_admin(request.user):
            return JsonResponse(
                {'error': 'Permission denied. Admin access only.'},
                status=403
            )

        export_format = request.GET.get('format', 'excel').lower()

        leaves = Leave.objects.filter(is_active=True)

        if export_format == 'excel':
            return self.export_excel(leaves)

        elif export_format == 'pdf':
            return self.export_pdf(leaves)

        else:
            return JsonResponse(
                {'error': 'Invalid format. Use "excel" or "pdf".'},
                status=400
            )

    # ---------------- EXCEL EXPORT ----------------
    def export_excel(self, leaves):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'Leave Report'

        ws.append([
            'Employee ID',
            'Employee Email',
            'Leave Type',
            'Status',
            'Start Date',
            'End Date'
        ])

        for leave in leaves:
            ws.append([
                leave.user.employee_id,
                leave.user.email,
                leave.leave_type,
                leave.status,
                str(leave.start_date),
                str(leave.end_date)
            ])

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="leave_report.xlsx"'

        wb.save(response)
        return response

    # ---------------- PDF EXPORT ----------------
    def export_pdf(self, leaves):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="leave_report.pdf"'

        doc = SimpleDocTemplate(response, pagesize=A4)
        elements = []

        data = [[
            'Employee ID',
            'Employee Email',
            'Leave Type',
            'Status',
            'Start Date',
            'End Date'
        ]]

        for leave in leaves:
            data.append([
                leave.user.employee_id,
                leave.user.email,
                leave.leave_type,
                leave.status,
                str(leave.start_date),
                str(leave.end_date)
            ])

        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ]))

        elements.append(table)
        doc.build(elements)

        return response