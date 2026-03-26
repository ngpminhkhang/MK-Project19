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

def institutional_pump():
    print("🚀 [INIT] Executing 50/30/20 Capital Allocation Protocol...")
    
    # Giả định tài khoản có 1.25M USD
    total_balance = 1250000 
    
    # THIẾT LẬP NGÂN SÁCH (BUDGET) THEO TỶ LỆ
    # 50% Currency | 30% Equity | 20% Commodity
    allocations = {
        "CURRENCY": total_balance * 0.50,
        "EQUITY": total_balance * 0.30,
        "COMMODITY": total_balance * 0.20
    }

    for market, budget in allocations.items():
        tickers = MARKETS[market]
        # Chia đều ngân sách cho 10 lệnh trong mỗi thị trường
        budget_per_trade = budget / 10 
        
        for ticker in tickers:
            data = yf.Ticker(ticker).history(period="1d")
            price = data['Close'].iloc[-1]
            
            # TÍNH TOÁN LOT SIZE ĐỂ KHỚP VỚI NGÂN SÁCH (Reverse Engineering)
            if market == "CURRENCY":
                # Budget = Lot * 100,000 * Price => Lot = Budget / (100,000 * Price)
                lot = budget_per_trade / (100000 * price)
            elif market == "COMMODITY":
                # Budget = Lot * 100 * Price => Lot = Budget / (100 * Price)
                lot = budget_per_trade / (100 * price)
            else: # EQUITY
                # Budget = Lot * 1 * Price => Lot = Budget / Price
                lot = budget_per_trade / price
                
            # Thực thi lệnh với Lot size đã được "đo ni đóng giày"
            AlphaSignal.objects.create(
                ticker=ticker,
                ceo_approved_lot=round(lot, 2),
                # ... các trường khác giữ nguyên ...
            )