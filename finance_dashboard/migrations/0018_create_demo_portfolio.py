from django.db import migrations

def create_demo_portfolio(apps, schema_editor):
    User = apps.get_model("auth", "User")
    Portfolio = apps.get_model("finance_dashboard", "Portfolio")

    # Tạo hoặc lấy admin user
    admin, created = User.objects.get_or_create(
        username="admin",
        defaults={
            "is_superuser": True,
            "is_staff": True,
            "email": "admin@example.com",
        }
    )
    if created:
        admin.set_password("Traucon123@")  # đổi lại sau khi login
        admin.save()

    # Tạo demo portfolio public
    Portfolio.objects.get_or_create(
        user=admin,
        name="Demo Portfolio",
        category="currency",
        symbol="EURUSD",
        amount=10000,
        is_public=True,
    )

def delete_demo_portfolio(apps, schema_editor):
    Portfolio = apps.get_model("finance_dashboard", "Portfolio")
    Portfolio.objects.filter(name="Demo Portfolio").delete()

class Migration(migrations.Migration):

    dependencies = [
        ("finance_dashboard", "0017_portfolio_is_public"),  # migration cuối cùng của bạn
    ]

    operations = [
        migrations.RunPython(create_demo_portfolio, delete_demo_portfolio),
    ]
