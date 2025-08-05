from django import forms
from .models import Video
from django.core.exceptions import ValidationError

class VideoSubmitForm(forms.ModelForm):

    class Meta:
        model = Video
        fields = ['title', 'description', 'non_category', 'video_file', 'thumbnail']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入作品标题（不超过50字）'
            }),
            'non_category': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '输入非遗类别（如：漆器、蜡染、傩戏、滚山珠...）',
                'list': 'category-suggestions'  # 添加数据列表
            }),
            'description': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': '请描述作品的创意和与非遗文化的关联'
            }),
            'video_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'video/mp4,video/webm'
            }),
            'thumbnail': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/jpeg,image/png'
            })
        }
        labels = {
            'title': '作品标题',
            'video_file': '上传视频',
            'thumbnail': '上传封面图',
            'description': '作品描述'
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['video_file'].help_text = '支持MP4/WebM格式，最大1GB'
        self.fields['thumbnail'].help_text = '推荐尺寸：1280×720像素，支持JPG/PNG格式'
        
    def clean_video_file(self):
        """视频文件验证"""
        video_file = self.cleaned_data.get('video_file')
        if video_file:
            # 文件大小验证 (最大1GB)
            if video_file.size > 1024 * 1024 * 1024:
                raise ValidationError("视频文件大小不能超过1GB")
            
            # 文件类型验证
            if not video_file.name.lower().endswith(('.mp4', '.webm')):
                raise ValidationError("只支持MP4或WebM格式")
        
        return video_file
    # forms.py 中添加验证
    def clean_non_category(self):
        category = self.cleaned_data.get('non_category', '').strip()
        
        if not category:
            raise ValidationError("请填写非遗类别")
        
        if len(category) > 20:
            raise ValidationError("类别名称过长（不超过20字）")
        
        # 添加常见非遗类别自动修正
        corrections = {
            '毕节漆器': '漆器',
            '蜡染工艺': '蜡染',
            '傩戏表演': '傩戏'
        }
        return corrections.get(category, category)

    def clean_thumbnail(self):
        """封面图验证"""
        thumbnail = self.cleaned_data.get('thumbnail')
        if thumbnail:
            # 文件大小验证 (最大5MB)
            if thumbnail.size > 5 * 1024 * 1024:
                raise ValidationError("封面图大小不能超过50MB")
            
            # 文件类型验证
            if not thumbnail.name.lower().endswith(('.jpg', '.jpeg', '.png')):
                raise ValidationError("只支持JPG或PNG格式")
        
        return thumbnail