# config/check_data.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from finance_dashboard.models import Portfolio, Trade
from django.contrib.auth.models import User

print("=== DATABASE CHECK ===")
print(f"Total Users: {User.objects.count()}")
print(f"Total Portfolios: {Portfolio.objects.count()}")
print(f"Total Trades: {Trade.objects.count()}")

print(f"\n=== PUBLIC PORTFOLIOS ===")
public_portfolios = Portfolio.objects.filter(is_public=True)
print(f"Public portfolios: {public_portfolios.count()}")

for portfolio in public_portfolios:
    trades = portfolio.trades.all()
    print(f"- {portfolio.name} (user: {portfolio.user}): {trades.count()} trades")
    for trade in trades[:3]:  # Hiển thị 3 trades đầu tiên
        print(f"  • {trade.symbol} - {trade.side} - {trade.date}")

print(f"\n=== ALL PORTFOLIOS ===")
all_portfolios = Portfolio.objects.all().select_related('user')
for portfolio in all_portfolios:
    print(f"- '{portfolio.name}' (public: {portfolio.is_public}, user: {portfolio.user.username}): {portfolio.trades.count()} trades")

print(f"\n=== KẾT LUẬN ===")
if public_portfolios.exists():
    print("✅ Có portfolio public - Khách nên thấy được")
else:
    print("❌ Không có portfolio public - Khách sẽ không thấy gì")
    print("💡 Cần tạo portfolio với is_public=True hoặc đổi portfolio có sẵn thành public")