from django.core.mail import send_mail
from django.conf import settings


def send_leave_status_email(leave, action):
    """
    action: 'APPROVED' or 'REJECTED'
    """

    subject = f"Leave Request {action}"

    message = f"""
Hello {leave.user.name},

Your leave request has been {action}.

Leave Type: {leave.leave_type}
Start Date: {leave.start_date}
End Date: {leave.end_date}
Status: {leave.status}

Approved By: {leave.approved_by.name}

Regards,
HR Team
"""

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[leave.user.email],
        fail_silently=False
    )
