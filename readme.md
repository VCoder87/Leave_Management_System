# Leave Management System (HRMS)

A comprehensive Human Resource Management System (HRMS) built with Django for managing employee leaves, roles, and profiles. This system streamlines the leave application process with role-based access control for Admins, Managers, and Employees.

## 🚀 Features

### 👤 Role-Based Access Control
- **Admin**: Full system access, dashboard overview.
- **Manager**: Approve/Reject leaves, view team dashboards, manage team documents.
- **Employee**: Apply for leaves, view leave history, manage profile.

### 📅 Leave Management
- **Apply for Leave**: Employees can apply for Casual and Sick.
- **Approval Workflow**: Managers can review and approve or reject leave requests.
- **Leave History**: Employees can track their past and current leave status.
- **Cancellation**: Option to cancel pending leave requests.
- **Document Support**: Upload supporting documents for sick leaves.

### 📊 Dashboards & Reporting
- **Manager Dashboard**: Overview of pending leaves and team status.
- **Admin Dashboard**: High-level view of system activities.
- **Export Data**: Export leave records to Excel/CSV for reporting.

### ⚙️ Profile Management
- **User Profiles**: Manage personal details.
- **Profile Pictures**: Upload and view profile images.

## 🛠️ Technology Stack

- **Backend**: Python, Django 6.0
- **Database**: PostgreSQL / SQLite (Configurable)
- **Authentication**: JWT 
- **Frontend**: Django Templates (HTML/CSS)

## 📦 Installation & Setup

Follow these steps to set up the project locally.

### Prerequisites
- Python 3.10+
- pip (Python package manager)

### 1. Clone the Repository
```bash
git clone https://github.com/VCoder87/Leave_Management_System
cd leave_management_system
```

### 2. Create and Activate Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the project root (`hrms/` directory) and add the following configurations:

```env
SECRET_KEY=your_secret_key_here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration (Optional - Defaults to SQLite if not set)
ENGINE=django.db.backends.postgresql
NAME=your_db_name
USER=your_db_user
DB_PASSWORD=your_db_password
HOST=localhost
PORT=5432

# Email Configuration (For notifications)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@example.com
EMAIL_HOST_PASSWORD=your_email_password
DEFAULT_FROM_EMAIL=your_email@example.com
```

### 5. Apply Migrations
```bash
python manage.py migrate
```

### 6. Create Superuser (Admin)
```bash
python manage.py createsuperuser
```

### 7. Run the Development Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser.

## 🔗 Key API Endpoints / Routes

| Feature | Endpoint | Description |
|---|---|---|
| **Login** | `/login/` | User login page |
| **Apply Leave** | `/leave/apply/` | Form to apply for new leave |
| **Leave History** | `/leave-history/` | View employee's leave history |
| **Manager Dashboard** | `/dashboard/manager/` | Manager's control panel |
| **Admin Dashboard** | `/admin_dashboard/` | Administrator's control panel |
| **Create Employee** | `/create-employee/` | Register new employee |
| **Export Leaves** | `/export/leaves/` | Download leave data |

## 🤝 Contributing

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/YourFeature`).
3. Commit your changes (`git commit -m 'Add some feature'`).
4. Push to the branch (`git push origin feature/YourFeature`).
5. Open a Pull Request.

