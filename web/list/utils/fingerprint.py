import hashlib

def generate_device_fingerprint(request):
    """生成设备唯一指纹"""
    # 收集设备特征
    device_data = {
        'ip': request.META.get('REMOTE_ADDR', ''),
        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        'accept_language': request.META.get('HTTP_ACCEPT_LANGUAGE', ''),
        'screen': request.POST.get('screen', '')  # 前端传递的屏幕分辨率
    }
    
    # 生成SHA256哈希作为设备指纹
    return hashlib.sha256(
        str(device_data).encode('utf-8')
    ).hexdigest()