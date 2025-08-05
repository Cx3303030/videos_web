from django.conf import settings
from django.core.mail import send_mail

def send_verify_code(email, code):
    """发送邮箱验证码"""
    subject = '验证你的邮箱'
    message = f'你的验证码是：{code}（5分钟内有效）'
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [email]
    
    return send_mail(subject, message, from_email, recipient_list)