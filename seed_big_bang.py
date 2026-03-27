import os
import django

# Đảm bảo đường dẫn này đúng với thư mục chứa settings.py của sếp
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings') 
django.setup()

from finance_dashboard.models import QuantAccount, PerformanceMetrics, BehaviorAudit

def big_bang_seeder():
    print("🚀 Khởi động Big Bang: Đang bơm dữ liệu 10 năm...")
    
    nodes = [
        {'name': 'Balanced Alpha', 'type': 'BALANCED', 'cap': 625225},
        {'name': 'Aggressive Growth', 'type': 'AGGRESSIVE', 'cap': 375135},
        {'name': 'Conservative Hedge', 'type': 'CONSERVATIVE', 'cap': 250090},
    ]

    for n in nodes:
        # CHỈ DÙNG 6 CỘT NÀY - KHÔNG THÊM BẤT CỨ GÌ KHÁC
        acc, _ = QuantAccount.objects.update_or_create(
            account_name=n['name'], 
            defaults={
                'strategy_type': n['type'],
                'balance': n['cap'], 
                'equity': n['cap'],
                'max_drawdown': 0.0,
                'current_drawdown': 0.0,
                'status': 'NORMAL'
            }
        )
        
        # Tạo Metrics cho Dashboard
        PerformanceMetrics.objects.update_or_create(
            account=acc,
            defaults={'win_rate': 68.5, 'oci_index': 0.84 if n['type']=='AGGRESSIVE' else 0.4}
        )

        # Bơm các vết sẹo lịch sử (Audit Logs)
        if n['type'] == 'AGGRESSIVE':
            events = [
                ("MACRO A BREACH", "COVID-19 Market Crash: Volatility Liquidation triggered."),
                ("OCI LOCKDOWN", "Post-Inflation Win Streak > 8. Forced size reduction."),
                ("MACRO B VIOLATION", "Geopolitical risk filter triggered (Eurodollar Spread).")
            ]
            for label, desc in events:
                BehaviorAudit.objects.get_or_create(
                    account=acc, 
                    event_label=label, 
                    defaults={'description': desc, 'severity': "CRITICAL"}
                )

    print("✅ BIG BANG HOÀN TẤT! Dữ liệu đã sẵn sàng trên Dashboard.")

if __name__ == "__main__":
    big_bang_seeder()