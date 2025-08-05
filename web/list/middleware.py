from django.http import JsonResponse
from django.utils import timezone
from .utils.fingerprint import generate_device_fingerprint
from .models import Vote

class VoteProtectionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # 只处理投票请求
        if request.path.startswith('/video/') and request.path.endswith('/vote/') and request.method == 'POST':
            # 生成设备指纹
            fingerprint = generate_device_fingerprint(request)
            one_hour_ago = timezone.now() - timezone.timedelta(hours=1)
            
            # 检查同一设备一小时内的投票次数
            device_votes = Vote.objects.filter(fingerprint=fingerprint, voted_at__gte=one_hour_ago).count()
            if device_votes >= 9:
                return JsonResponse({
                    'status': 'error',
                    'message': '疑似刷票，封禁一小时，有疑问请联系管理员'
                }, status=403)
            
            today = timezone.now().date()
            
            # 已在views.py中实现按用户账号的投票限制
            # 此处不再重复限制
            pass
        
        return self.get_response(request)