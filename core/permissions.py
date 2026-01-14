def is_admin(user):
    return user.role and user.role.role_name == 'ADMIN'


def is_manager(user):
    return user.role and user.role.role_name == 'MANAGER'


def is_employee(user):
    return user.role and user.role.role_name == 'EMPLOYEE'
