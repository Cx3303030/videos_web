from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.defaults import page_not_found, server_error

urlpatterns = [
    path('admin/', admin.site.urls),
    path('videos/', include('list.urls')),
]

# 错误处理器
handler404 = 'list.views.custom_404'
handler500 = 'list.views.custom_500'

# 配置静态文件和媒体文件访问
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
