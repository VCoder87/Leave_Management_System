from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager
)

# ---------------- ROLE MODEL ----------------
class Role(models.Model):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('MANAGER', 'Manager'),
        ('EMPLOYEE', 'Employee'),
    )

    role_name = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        unique=True
    )

    def __str__(self):
        return self.role_name


# ---------------- USER MANAGER ----------------
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, role=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')

        if role is None:
            raise ValueError('Role is required')

        email = self.normalize_email(email)
        user = self.model(email=email, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        admin_role, _ = Role.objects.get_or_create(role_name='ADMIN')

        user = self.create_user(
            email=email,
            password=password,
            role=admin_role,
            **extra_fields
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


# ---------------- USER MODEL ----------------
class User(AbstractBaseUser, PermissionsMixin):
    employee_id = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True
    )

    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)

    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT
    )

    manager = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='team_members'
    )

    # ✅ PROFILE IMAGE FIELD (FIXED)
    profile_image = models.ImageField(
        upload_to='profiles/',
        null=True,
        blank=True
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()
    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.email


# ---------------- LEAVE MODEL ----------------
class Leave(models.Model):
    LEAVE_TYPES = (
        ('CASUAL', 'Casual'),
        ('SICK', 'Sick'),
        ('EARNED', 'Earned'),
    )

    STATUS = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    leave_type = models.CharField(
        max_length=20,
        choices=LEAVE_TYPES
    )

    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default='PENDING'
    )

    approved_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        related_name='approved_leaves',
        on_delete=models.SET_NULL
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ✅ SOFT DELETE FLAG
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.email} - {self.leave_type} ({self.status})"


# ---------------- LEAVE DOCUMENT ----------------
class LeaveDocument(models.Model):
    leave = models.ForeignKey(
        Leave,
        on_delete=models.CASCADE,
        related_name='documents'
    )

    file = models.FileField(upload_to='leave_docs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Document for Leave ID {self.leave.id}"
