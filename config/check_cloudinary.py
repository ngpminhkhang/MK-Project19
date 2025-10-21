# config/check_cloudinary.py
import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

print("=== CLOUDINARY CONFIG CHECK ===")
print(f"CLOUD_NAME: {os.environ.get('CLOUDINARY_CLOUD_NAME')}")
print(f"API_KEY: {os.environ.get('CLOUDINARY_API_KEY')}")
print(f"API_SECRET: {'*' * len(os.environ.get('CLOUDINARY_API_SECRET', ''))}")

print(f"\n=== DJANGO SETTINGS ===")
print(f"DEFAULT_FILE_STORAGE: {getattr(settings, 'DEFAULT_FILE_STORAGE', 'Not set')}")

# Kiểm tra installed apps
cloudinary_apps = [app for app in settings.INSTALLED_APPS if 'cloudinary' in app]
print(f"Cloudinary apps: {cloudinary_apps}")

# Kiểm tra xem có đang dùng local storage không
if hasattr(settings, 'MEDIA_ROOT'):
    print(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")
    print("⚠️  Đang sử dụng LOCAL storage (MEDIA_ROOT được set)")
else:
    print("✅ Không có MEDIA_ROOT - Có thể đang dùng Cloudinary")

print(f"\n=== KẾT LUẬN ===")
cloudinary_configured = all([
    os.environ.get('CLOUDINARY_CLOUD_NAME'),
    os.environ.get('CLOUDINARY_API_KEY'), 
    os.environ.get('CLOUDINARY_API_SECRET')
])

if cloudinary_configured:
    print("✅ Cloudinary environment variables: ĐẦY ĐỦ")
else:
    print("❌ Cloudinary environment variables: THIẾU")

if 'cloudinary_storage' in settings.INSTALLED_APPS:
    print("✅ Cloudinary apps: ĐÃ CÀI ĐẶT")
else:
    print("❌ Cloudinary apps: CHƯA CÀI ĐẶT")