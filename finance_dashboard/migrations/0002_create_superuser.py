from django.db import migrations
from django.contrib.auth.hashers import make_password


def create_admin(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    if not User.objects.filter(username="admin").exists():
        User.objects.create(
            username="admin",
            password=make_password("Traucon123@"),  # ⚡ đổi mật khẩu tại đây nếu muốn
            is_superuser=True,
            is_staff=True,
            email="angpminhkhang@gmail.com"
        )


def delete_admin(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    User.objects.filter(username="admin").delete()


class Migration(migrations.Migration):

    dependencies = [
        ('finance_dashboard', '0001_initial'),  # Đảm bảo chạy sau khi tạo bảng
    ]

    operations = [
        migrations.RunPython(create_admin, delete_admin),
    ]
