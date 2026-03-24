from django.urls import re_path
from . import consumers

# Định nghĩa các tuyến đường cho WebSocket
websocket_urlpatterns = [
    # Đường dây nóng đẩy dữ liệu AUM Terminal
    re_path(r'ws/terminal/(?P<account_id>\w+)/$', consumers.TerminalConsumer.as_asgi()),
    # Đường dây đẩy tín hiệu Radar trực tiếp
    re_path(r'ws/radar/$', consumers.RadarConsumer.as_asgi()),
]