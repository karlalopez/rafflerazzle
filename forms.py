from wtforms import Form, BooleanField, StringField, PasswordField, validators

class UserForm(Form):
    email = StringField('Email address', [validators.Length(min=6, max=35)])
    password = PasswordField('Password', [
        validators.Required(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Confirm password')


class LoginForm(Form):
    email = StringField('Email address', [validators.Length(min=6, max=35)])
    password = PasswordField('Password')

class ChangePasswordForm(Form):
    old_password = PasswordField('Old password')
    new_password = PasswordField('New password', [
        validators.Required(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Confirm new password')

class ForgotPasswordForm(Form):
    email = StringField('Email address', [validators.Length(min=6, max=35)])

class AddUserForm(Form):
    email = StringField('Email address', [validators.Length(min=6, max=35)])


class ResetPasswordForm(Form):
    new_password = PasswordField('New password', [
        validators.Required(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Confirm new password')