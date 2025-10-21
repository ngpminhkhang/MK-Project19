from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(template_name='finance_dashboard/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Include all app URLs from finance_dashboard - SỬA DÒNG NÀY
    path('', include('finance_dashboard.urls')),  # SỬA: './' → ''
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# config/urls.py - THÊM VÀO CUỐI FILE
from django.urls import path
from . import debug_views  # Sẽ tạo file này

urlpatterns = [
    # ... các URL hiện có ...
    
    # Debug URLs - THÊM 2 DÒNG NÀY
    path('debug/cloudinary/', debug_views.debug_cloudinary, name='debug_cloudinary'),
    path('debug/database/', debug_views.debug_database, name='debug_database'),
]