# config/asgi.py
import os
import django
from django.core.asgi import get_asgi_application

# 1. Phải đặt biến môi trường và setup Django TRƯỚC khi import bất kỳ thứ gì khác
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# 2. Khởi tạo ứng dụng HTTP truyền thống
django_asgi_app = get_asgi_application()

# 3. Sau đó mới import các module WebSocket
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import finance_dashboard.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app, # Luồng Admin/Web bình thường
    "websocket": AuthMiddlewareStack(
        URLRouter(
            finance_dashboard.routing.websocket_urlpatterns
        )
    ),
})