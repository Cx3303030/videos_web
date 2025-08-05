from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from . import views

urlpatterns = [
    # 静态资源测试视图
    path('static-test/', views.static_test, name='static_test'),
    # 首页视图
    path('home/', views.home, name='home'),
    # 处理accounts/login/请求，映射到自定义email_login视图
    path('accounts/login/', views.email_login, name='login'),
    # 视频主页面
    path('', views.videos_page, name='videos_home'),
    
    path('login/email/', views.email_login, name='email_login'),
    # 页面三个主要模块
    path('info/', views.competition_info, name='competition_info'),
    path('list/', views.video_list, name='video_list'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('team-showcase/', views.team_showcase, name='team_showcase'),

    path('leaderboard/api/', views.leaderboard_api, name='leaderboard_api'),
    
    # 视频详情页
    path('video/<int:pk>/', views.video_detail, name='video_detail'),
    
    # 投票接口
    path('vote/<int:pk>/', views.vote, name='video_vote'),
    path('vote_video/<int:pk>/', views.vote_video, name='vote_video'),
    # 检查投票接口
    path('check-votes/', views.check_votes, name='check_votes'),
    # 投稿接口
    path('submit/', views.submit_video, name='submit_video'),
     # 登录登出相关
    path('login/', views.email_login, name='direct_login'),
    path('logout/confirm/', views.custom_logout, name='logout_confirm'),
    path('logout/', views.custom_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-code/', views.verify_code, name='verify_code'),
    path('reset-password/', views.reset_password, name='reset_password'),
    
    path('send-verification-code/', views.send_verification_code_view, name='send_verification_code'),
    path('send-registration-code/', views.send_registration_code, name='send_registration_code'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])