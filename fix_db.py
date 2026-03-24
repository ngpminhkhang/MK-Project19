import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def fix_missing_column():
    with connection.cursor() as cursor:
        try:
            print("Đang tiến hành cấy ghép cột account_name...")
            cursor.execute('ALTER TABLE finance_dashboard_quantaccount ADD COLUMN account_name VARCHAR(255) DEFAULT \'Main Account\';')
            print("✅ Cấy ghép thành công! Cột account_name đã xuất hiện.")
        except Exception as e:
            print(f"❌ Thất bại hoặc cột đã tồn tại: {e}")

if __name__ == "__main__":
    fix_missing_column()