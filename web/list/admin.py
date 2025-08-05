from django.contrib import admin
from .models import Video, Vote, MediaAsset

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'created_at', 'is_approved']  # 使用模型中实际存在的字段
    list_filter = ['is_approved', 'created_at']  # 使用模型中实际存在的字段
    search_fields = ('title', 'description')

@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'video', 'voted_at')

admin.site.register(MediaAsset)