import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def nuke_all_tables():
    with connection.cursor() as cursor:
        print("🚀 Đang quét sạch toàn bộ chiến trường app finance_dashboard...")
        # Lệnh SQL để xóa sạch mọi bảng có tiền tố finance_dashboard_
        cursor.execute("""
            DO $$ DECLARE
                r RECORD;
            BEGIN
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE 'finance_dashboard_%') LOOP
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END $$;
        """)
        # Xóa sạch lịch sử migration của app này
        cursor.execute("DELETE FROM django_migrations WHERE app = 'finance_dashboard';")
        print("✅ Đã san phẳng! Không còn một dấu vết nào của bảng cũ.")

if __name__ == "__main__":
    nuke_all_tables()