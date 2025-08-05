from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import os
import uuid

User = get_user_model()

# 安全文件名生成器
def safe_filename(instance, filename):
    ext = filename.split('.')[-1]
    new_name = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join('videos', new_name)

class Video(models.Model):
    title = models.CharField('作品标题', max_length=200)
    description = models.TextField('作品描述')
    non_category = models.CharField(
        '非遗类别', 
        max_length=50,  # 增加长度限制
        blank=True,     # 允许为空
        help_text='请输入作品涉及的非遗类别（如：漆器、蜡染、傩戏等）'
    )
    # 使用安全文件名处理器
    video_file = models.FileField('视频文件', upload_to=safe_filename)
    thumbnail = models.ImageField('封面图', upload_to='thumbnails/', null=True, blank=True)
    
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='投稿人')
    votes = models.PositiveIntegerField('点赞数', default=0)
    created_at = models.DateTimeField('投稿时间', auto_now_add=True)
    is_approved = models.BooleanField('审核通过', default=False)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-votes']  # 默认按点赞数排序
        
class Vote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    video = models.ForeignKey('Video', on_delete=models.CASCADE)
    voted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'video', 'voted_at']),  # 添加复合索引提高查询效率
            models.Index(fields=['user', 'voted_at']),
        ]
    
    @classmethod
    def user_can_vote_today(cls, user):
        """检查用户今天是否已投票"""
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return cls.objects.filter(user=user, voted_at__gte=today_start).exists()


class MediaAsset(models.Model):
    ASSET_TYPES = (
        ('video', '视频'),
        ('image', '图片'),
        ('qrcode', '二维码'),
    )
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPES)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='media_assets/%Y/%m/')