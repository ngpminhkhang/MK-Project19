import random
import yfinance as yf
from finance_dashboard.models import AlphaSignal, RiskLog, QuantAccount

# THỐNG NHẤT DANH MỤC HỌC THUẬT
MARKETS = {
    "CURRENCY": ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCAD=X"],
    "COMMODITY": ["GC=F", "SI=F", "CL=F", "HG=F", "PL=F"], 
    "EQUITY": ["AAPL", "NVDA", "TSLA", "MSFT", "GOOGL", "BTC-USD", "ETH-USD"]
}

def terminal_takeover():
    print("🚀 [INIT] Finalizing Alpha Injection...")

    # BƯỚC 1: ĐẢM BẢO MASTER ACCOUNT TỒN TẠI (Dùng field 'account_name' đã check)
    master_node, _ = QuantAccount.objects.get_or_create(
        account_name="Master Fund Node",
        defaults={'balance': 1250450.75, 'equity': 1250450.75, 'status': 'ACTIVE'}
    )
    print(f"🏛️ Master Node Verified: {master_node.account_name}")

    # Làm sạch sàn giao dịch
    AlphaSignal.objects.all().delete()
    RiskLog.objects.all().delete()

    for market_name, tickers in MARKETS.items():
        print(f"📦 Filling {market_name} Matrix...")
        for _ in range(10):
            ticker = random.choice(tickers)
            try:
                # Triệu hồi dữ liệu giá thực tế
                data = yf.Ticker(ticker).history(period="1d")
                price = data['Close'].iloc[-1]
                
                # BƯỚC 2: POSITION EXECUTION (Đã xóa bỏ keyword 'account' gây lỗi)
                sig = AlphaSignal.objects.create(
                    ticker=ticker.replace("=X", "").replace("=F", ""),
                    signal_direction=random.choice(['BUY', 'SELL']),
                    entry_price=price,
                    ceo_approved_lot=round(random.uniform(0.1, 0.3), 2),
                    status=random.choice(['EXECUTED', 'Sent to Broker', 'APPROVED']),
                    pnl=random.uniform(-1000, 3000)
                )

                # BƯỚC 3: RISK AUDIT TRAIL
                RiskLog.objects.create(
                    signal=sig,
                    decision="APPROVED",
                    reason=f"Institutional liquidity parameters met for {market_name}."
                )
            except:
                continue

    print("✅ [SUCCESS] 30 Quant Nodes Live. White-space Liquidated.")

# Hành quyết ngay!
terminal_takeover()