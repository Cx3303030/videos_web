import secrets
import string
import random
# 会话密钥常量
SESSION_KEY = 'registration_email_code'
from django.shortcuts import render, get_object_or_404, redirect
from django.core.mail import send_mail
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from .forms import VideoSubmitForm

# 从设置中获取每日最大投票数
MAX_VOTES_PER_DAY = getattr(settings, 'SECURITY_SETTINGS', {}).get('MAX_VOTES_PER_DAY', 1)
from django.contrib.auth.decorators import login_required
from .models import Video, Vote
from django.db.models import F
from django.db import transaction
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.utils import timezone 
from .utils.fingerprint import generate_device_fingerprint
from django.views.decorators.http import require_POST
from django.views.decorators.cache import cache_page
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .utils.email import send_verify_code


def videos_page(request):
    """视频主页面，包含三个模块"""
    return render(request, 'list/videos.html')

def competition_info(request):
    """比赛介绍页面"""
    return render(request, 'list/competition_info.html')

def video_list(request):
    """视频列表页面 - 显示封面、投稿人、点赞数，支持搜索"""
    # 获取搜索参数
    search_query = request.GET.get('search', '')
    
    # 基本查询：只显示已审核的视频
    videos = Video.objects.filter(is_approved=True).select_related('author')
    
    # 如果有搜索参数，过滤标题包含搜索词的视频
    if search_query:
        videos = videos.filter(title__icontains=search_query)
        
    return render(request, 'list/video_list.html', {
        'videos': videos,
        'search_query': search_query
    })

def check_votes(request):
    """检查用户今日剩余票数"""
    # 只有登录用户才能投票
    if not request.user.is_authenticated:
        return JsonResponse({
            'remaining_votes': 0,
            'max_votes': MAX_VOTES_PER_DAY,
            'error': '请先登录才能投票'
        })
    
    # 获取今日日期（仅日期部分）
    today = timezone.now().date()
    
    # 计算今日已投票数
    daily_votes = Vote.objects.filter(
        user=request.user,
        voted_at__date=today
    ).count()
    
    # 计算剩余票数
    remaining_votes = MAX_VOTES_PER_DAY - daily_votes
    
    return JsonResponse({
        'remaining_votes': remaining_votes,
        'max_votes': MAX_VOTES_PER_DAY
    })

def video_detail(request, pk):
    """视频详情页 - 显示视频、排名信息、投票功能"""
    video = get_object_or_404(Video, pk=pk, is_approved=True)
    
    # 计算当前排名（所有审核通过的视频中点赞数多于当前视频的数量+1）
    rank = Video.objects.filter(
        is_approved=True, 
        votes__gt=video.votes
    ).count() + 1
    
    # 检查当前用户今日是否已投票
    user_voted = False
    if request.user.is_authenticated:
        today = timezone.now().date()
        user_voted = Vote.objects.filter(
            user=request.user, 
            video=video,
            voted_at__date=today
        ).exists()
    
    return render(request, 'list/video_detail.html', {
        'video': video,
        'rank': rank,
        'user_voted': user_voted
    })

def leaderboard(request):
    """排行榜页面"""
    # 获取排名前100的视频
    top_videos = Video.objects.filter(
        is_approved=True
    ).order_by('-votes')[:100]
    
    return render(request, 'list/leaderboard.html', {'videos': top_videos})

@cache_page(30)  # 缓存1秒，减少数据库压力
def leaderboard_api(request):
    # 获取最新排名数据
    videos = Video.objects.filter(is_approved=True).order_by('-votes')[:20]
    
    # 准备返回数据
    video_list = []
    for i, video in enumerate(videos):
        # 计算排名变化（简化示例，实际中需要存储历史排名）
        rank_change = 0  # 此处应根据历史数据计算
        vote_change = 0  # 此处应根据历史数据计算
        
        video_data = {
            'id': video.id,
            'title': video.title,
            'thumbnail': video.thumbnail.url if video.thumbnail else '',
            'non_category': video.non_category,
            'author': video.author.username,
            'votes': video.votes,
            'rank_change': rank_change,
            'vote_change': vote_change
        }
        video_list.append(video_data)
    
    return JsonResponse({
        'videos': video_list,
        'last_updated': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@login_required(login_url='login')
@transaction.atomic
def submit_video(request):
    # 检查用户投稿限制
    user_video_count = Video.objects.filter(author=request.user).count()
    if user_video_count >= 3:
        messages.warning(request, "每个用户最多投稿3个作品")
        return redirect('video_list')
    
    if request.method == 'POST':
        form = VideoSubmitForm(request.POST, request.FILES)
        if form.is_valid():
            video = form.save(commit=False)
            video.author = request.user
            # 自动审核通过
            video.is_approved = True
            video.save()
            
            # 添加成功消息
            messages.success(request, "作品已成功发布！")
            return redirect('video_detail', pk=video.pk)
    else:
        form = VideoSubmitForm()
    
    return render(request, 'list/submit_video.html', {'form': form})
    
@login_required(login_url='login')
def vote(request, pk):
    """投票视图（Ajax调用）"""
    video = get_object_or_404(Video, pk=pk, is_approved=True)
    
    # 检查用户是否已投过票
    if Vote.objects.filter(user=request.user, video=video).exists():
        return JsonResponse({
            'status': 'error', 
            'message': '您已经投过票了'
        })
    
    # 创建投票记录
    Vote.objects.create(user=request.user, video=video)
    
    # 原子操作更新视频票数
    Video.objects.filter(pk=video.pk).update(votes=F('votes') + 1)
    
    # 重新计算排名
    rank = Video.objects.filter(
        is_approved=True, 
        votes__gt=video.votes
    ).count() + 2  # 加2因为+1是本视频，再加1是排名进位
    
    return JsonResponse({
        'status': 'success',
        'new_votes': video.votes + 1,
        'rank': rank
    })

# 添加首页视图
def home(request):
    """处理根路径请求，展示首页内容"""
    context = {}
    # 当访问根路径时，设置标志以在base.html中显示首页内容
    if request.path == '/':
        context['is_home'] = True
        # context['featured_videos'] = Video.objects.filter(is_approved=True).order_by('-votes')[:3]
    
    return render(request, 'list/base.html', context)

# 静态资源测试视图
def static_test(request):
    """测试静态资源配置"""
    return render(request, 'list/static_test.html')

def custom_logout(request):
    if request.method == 'POST':
        logout(request)
        messages.info(request, "您已成功退出登录")
        return redirect('home')
    return render(request, 'registration/logout_confirm.html')
# 修改投票视图
@require_POST
@login_required(login_url='login')
def vote_video(request, pk):
    """投票视图"""
    video = get_object_or_404(Video, pk=pk)
    
    today = timezone.now().date()
    one_hour_ago = timezone.now() - timezone.timedelta(hours=1)
    
    # 检查今天已投票数
    daily_votes = Vote.objects.filter(user=request.user, voted_at__date=today).count()
    remaining_votes = MAX_VOTES_PER_DAY - daily_votes
    
    # 检查同一作品一小时内的投票次数
    video_votes = Vote.objects.filter(video=video, voted_at__gte=one_hour_ago).count()
    if video_votes >= 300:
        return JsonResponse({
            'status': 'error', 
            'message': '疑似刷票，封禁一小时，请联系管理员',
            'remaining_votes': 0
        })
    
    # 检查是否已达到投票上限
    if daily_votes >= MAX_VOTES_PER_DAY:
        return JsonResponse({
            'status': 'error', 
            'message': f'投票失败，今日剩余0票',
            'remaining_votes': 0
        })
    
    # 检查是否已经给这个视频投过票（今天）
    if Vote.objects.filter(user=request.user, video=video, voted_at__date=today).exists():
        return JsonResponse({
            'status': 'error', 
            'message': '您已经给这个视频投过票了',
            'remaining_votes': remaining_votes
        })
    
    # 创建投票记录
    Vote.objects.create(
        user=request.user,
        video=video
    )
    
    # 使用F表达式原子更新视频票数，避免并发问题
    Video.objects.filter(pk=video.pk).update(votes=F('votes') + 1)
    # 重新获取视频对象以获取最新票数
    video = Video.objects.get(pk=video.pk)
    
    remaining_votes -= 1
    
    return JsonResponse({
        'status': 'success',
        'new_count': video.votes,
        'message': f'您已成功投票，今日剩余{remaining_votes}票',
        'remaining_votes': remaining_votes
    })

def register(request):
    
    if request.method == 'POST':
        step = request.POST.get('step', 'form')
        
        # 步骤1：处理表单提交
        if step == 'form':
            username = request.POST['username']
            email = request.POST['email']
            password = request.POST['password']
            
            # 验证用户名是否存在
            if User.objects.filter(username=username).exists():
                messages.error(request, '用户名已存在！')
                return redirect('register')
            
            # 验证邮箱是否存在
            if User.objects.filter(email=email).exists():
                messages.error(request, '邮箱已被注册！')
                return redirect('register')

            # 生成6位验证码
            code = ''.join(random.choices(string.digits, k=6))
            
            # 发送邮件
            subject = '注册验证码 - 视频投稿平台'
            message = f'您的注册验证码是：{code}\n有效期5分钟，请尽快完成验证。'
            from_email = settings.EMAIL_HOST_USER
            
            try:
                send_mail(subject, message, from_email, [email])
                # 将验证码和邮箱存入session
                request.session[SESSION_KEY] = {
                    'code': code,
                    'email': email,
                    'timestamp': timezone.now().isoformat()  # 转换为ISO格式字符串
                }
                messages.success(request, '验证码已发送至您的邮箱，请查收。')
                return render(request, 'registration/register.html', {
                    'step': 'verify',
                    'username': username,
                    'email': email,
                    'password': password
                })
            except Exception as e:
                messages.error(request, f'发送验证码失败：{str(e)}')
                return redirect('register')
        
        # 步骤2：处理验证码验证
        elif step == 'verify':
            user_code = request.POST.get('code')
            session_data = request.session.get(SESSION_KEY)
            
            if not session_data:
                messages.error(request, '验证码已过期，请重新获取。')
                return redirect('register')
            
            # 验证验证码是否正确
            if user_code != session_data['code']:
                messages.error(request, '验证码错误，请重新输入。')
                return render(request, 'registration/register.html', {
                    'step': 'verify',
                    'username': request.POST['username'],
                    'email': request.POST['email'],
                    'password': request.POST['password']
                })
            
            # 验证邮箱是否匹配
            if request.POST['email'] != session_data['email']:
                messages.error(request, '邮箱地址不匹配。')
                return redirect('register')
            
            # 验证是否超时（5分钟）
            try:
                # 将ISO格式字符串转换回datetime对象
                timestamp = timezone.datetime.fromisoformat(session_data['timestamp'])
                if (timezone.now() - timestamp).total_seconds() > 300:
                    messages.error(request, '验证码已过期，请重新获取。')
                    return redirect('register')
            except ValueError:
                messages.error(request, '验证码格式错误，请重新获取。')
                return redirect('register')
            
            # 创建用户
            try:
                user = User.objects.create_user(
                    username=request.POST['username'],
                    email=request.POST['email'],
                    password=request.POST['password']
                )
                user.save()
                messages.success(request, '注册成功！请登录。')
                
                # 清除session中的验证码
                del request.session[SESSION_KEY]
                
                return redirect('login')
            except Exception as e:
                messages.error(request, f'注册失败：{str(e)}')
        else:
            # 处理未知的step值
            messages.error(request, '无效的请求步骤')
            return redirect('register')
    
    # 默认返回注册表单页面
    return render(request, 'registration/register.html', {'step': 'form'})

def email_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('videos_home')  # 重定向到 /videos/ 页面
        else:
            messages.error(request, '用户名或密码错误！')
    
    return render(request, 'registration/login_email.html')

def send_verification_code_view(request):
    email = request.GET.get('email')
    if email:
        # 生成验证码
        code = ''.join(secrets.choice(string.digits) for i in range(6))
        send_verify_code(email, code)
        request.session['verification_code'] = code
        return JsonResponse({'status': 'success', 'message': '验证码已发送'})
    return JsonResponse({'status': 'error', 'message': '请提供有效的邮箱地址'})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, '用户名或密码错误！')
    
    return render(request, 'registration/login.html')

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST['email']
        try:
            user = User.objects.get(email=email)
            # 生成随机验证码
            code = ''.join(random.choices(string.digits, k=6))
            request.session['reset_code'] = code
            request.session['reset_email'] = email
            
            # 发送邮件
            subject = '重置密码验证码'
            message = f'您的验证码是：{code}'
            from_email = settings.EMAIL_HOST_USER
            send_mail(subject, message, from_email, [email])
            
            return redirect('verify_code')
        except User.DoesNotExist:
            messages.error(request, '该邮箱未注册！')
    
    return render(request, 'registration/forgot_password.html')

def send_code(request):
    email = request.GET.get('email')
    code = ''.join(secrets.choice(string.digits) for i in range(6))
    send_verify_code(email, code)
    return HttpResponse('验证码已发送')

def send_registration_code(request):
    # 注意：此函数存储的验证码时间戳使用ISO格式字符串
    # 在验证时需要先转换为datetime对象
    email = request.GET.get('email')
    if not email:
        return JsonResponse({'status': 'error', 'message': '请提供邮箱地址'})
    # 生成6位验证码
    code = ''.join(random.choices(string.digits, k=6))
    # 发送邮件
    subject = '注册验证码 - 视频投稿平台'
    message = f'您的注册验证码是：{code}\n有效期5分钟，请尽快完成验证。'

    try:
        from_email = settings.EMAIL_HOST_USER
        send_mail(subject, message, from_email, [email])
        # 将验证码和邮箱存入session
        request.session['registration_email_code'] = {
            'code': code,
            'email': email,
            'timestamp': timezone.now().isoformat()  # 转换为ISO格式字符串
        }    
        return JsonResponse({'status': 'success', 'message': '验证码已发送'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'发送失败：{str(e)}'})

def verify_code(request):
    if request.method == 'POST':
        code = request.POST.get('code')
        reset_code = request.session.get('reset_code')
        reset_email = request.session.get('reset_email')
        
        if not reset_code or not reset_email:
            messages.error(request, '验证码已过期，请重新获取。')
            return redirect('forgot_password')
        
        if code == reset_code:
            # 验证码正确，重定向到重置密码页面
            return redirect('reset_password')
        else:
            messages.error(request, '验证码错误，请重新输入。')
    
    return render(request, 'registration/verify_code.html')

def reset_password(request):
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        reset_email = request.session.get('reset_email')
        
        if not reset_email:
            messages.error(request, '会话已过期，请重新开始密码重置流程。')
            return redirect('forgot_password')
        
        if new_password != confirm_password:
            messages.error(request, '两次输入的密码不一致，请重新输入。')
            return render(request, 'registration/reset_password.html')
        
        try:
            user = User.objects.get(email=reset_email)
            user.set_password(new_password)
            user.save()
            
            # 清除session中的重置信息
            del request.session['reset_code']
            del request.session['reset_email']
            
            messages.success(request, '密码已成功重置，请使用新密码登录。')
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, '用户不存在，请重新开始密码重置流程。')
            return redirect('forgot_password')
    
    return render(request, 'registration/reset_password.html')

def team_showcase(request):
    """小队展示页面"""
    # 这里实际开发中应该从数据库获取管理员上传的内容
    # 示例数据
    themes = [
        {
            'name': '滚山珠',
            'video_url': '/static/sample_videos/gunshanzhu.mp4',
            'images': ['/static/sample_images/gunshanzhu1.jpg', '/static/sample_images/gunshanzhu2.jpg']
        },
        {
            'name': '傩戏',
            'video_url': '/static/sample_videos/nuoxi.mp4',
            'images': ['/static/sample_images/nuoxi1.jpg', '/static/sample_images/nuoxi2.jpg']
        },
        {
            'name': '大方漆器',
            'video_url': '/static/sample_videos/lacquer.mp4',
            'images': ['/static/sample_images/lacquer1.jpg', '/static/sample_images/lacquer2.jpg']
        },
        {
            'name': '蜡染',
            'video_url': '/static/sample_videos/batik.mp4',
            'images': ['/static/sample_images/batik1.jpg', '/static/sample_images/batik2.jpg']
        }
    ]
    
    return render(request, 'list/team_showcase.html', {
        'themes': themes
    })


# 自定义错误处理视图
def custom_404(request, exception):
    return render(request, 'list/404.html', status=404)

def custom_500(request):
    return render(request, 'list/500.html', status=500)
            