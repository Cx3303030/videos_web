from django.conf import settings
from django.core.mail import EmailMessage

def send_verify_code(email, code):
    """发送邮箱验证码"""
    subject = '验证你的邮箱'
    message = f'你的验证码是：{code}（5分钟内有效）'
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [email]
    
    # 使用EmailMessage类并明确设置UTF-8编码
    email_message = EmailMessage(
        subject=subject,
        body=message,
        from_email=from_email,
        to=recipient_list,
    )
    email_message.content_subtype = 'html'
    email_message.encoding = 'utf-8'
    
    return email_message.send()