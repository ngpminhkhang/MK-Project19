import json, logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.core.cache import cache
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from tenacity import retry, stop_after_attempt, wait_fixed
from .risk_services import process_oci_impact

# Import Models & Engines
from .models import (
    Portfolio, Trade, ForexPair, Insight, WeeklyOutlook,
    QuantAccount, AlphaSignal, MacroDirective, RadarBlip, WeeklyReview, MissedTrade, RiskLog
)
from .risk_engine import KellyEngine, CentralRiskEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==========================================
# 1. TRỢ THỦ DỮ LIỆU & CACHE (HELPERS)
# ==========================================

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def _yf_last_and_change(symbol: str):
    import yfinance as yf
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="2d", interval="1d")
    if not hist.empty:
        last = float(hist["Close"].iloc[-1])
        if len(hist) > 1:
            prev = float(hist["Close"].iloc[-2])
            change_pct = round(((last - prev) / prev) * 100, 2) if prev else None
        else:
            change_pct = None
        return {"last": last, "change": change_pct}
    raise ValueError(f"No data for {symbol}")

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def _yf_sparkline(symbol: str, points: int = 20):
    import yfinance as yf
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="1mo", interval="1d")
    if not hist.empty:
        closes = hist["Close"].dropna().tail(points).astype(float).tolist()
        return closes if closes else None
    raise ValueError(f"No sparkline for {symbol}")

def get_symbol_data(symbol, timeout=1800):
    key = f"symbol_{symbol}"
    data = cache.get(key)
    if data: return data
    try:
        data = _yf_last_and_change(symbol)
        cache.set(key, data, timeout=timeout)
        return data
    except Exception as e:
        logger.error(f"Error getting symbol data for {symbol}: {e}")
        return {"last": None, "change": None}

def get_multiple_chart_data(pairs=('EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD'), timeout=3600):
    chart_data = {}
    for pair in pairs:
        cache_key = f"chart_data_{pair}"
        cached_data = cache.get(cache_key)
        if cached_data:
            chart_data[pair] = cached_data
            continue
        try:
            import yfinance as yf
            yf_symbol = pair + '=X' if not pair.endswith('=X') else pair
            ticker = yf.Ticker(yf_symbol)
            hist = ticker.history(period="30d", interval="1d")
            if not hist.empty:
                decimals = 3 if 'JPY' in pair else 5
                values = [round(float(v), decimals) for v in hist["Close"].tolist()]
                data = {
                    "labels": [d.strftime("%Y-%m-%d") for d in hist.index],
                    "values": values,
                    "high": round(float(hist["High"].max()), decimals),
                    "low": round(float(hist["Low"].min()), decimals),
                    "volume": "High" if hist["Volume"].mean() > 1000000 else "Medium"
                }
                chart_data[pair] = data
                cache.set(cache_key, data, timeout=timeout)
        except Exception:
            chart_data[pair] = {"labels": [], "values": []}
    return chart_data

# ==========================================
# 2. TẦNG WEBSITE TRUYỀN THỐNG
# ==========================================

def home(request):
    indices_symbols = {"DXY": "DX-Y.NYB", "SP500": "^GSPC", "US10Y": "^TNX", "Gold": "GC=F"}
    indices = {name: get_symbol_data(sym).get("last") for name, sym in indices_symbols.items()}
    
    chart_pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD']
    forex_data = []
    for pair in chart_pairs:
        raw = get_symbol_data(pair + "=X")
        forex_data.append({"pair": pair, "last": raw["last"], "change": raw["change"]})

    context = {
        "indices": indices,
        "forex_data": forex_data,
        "risk_on": True,
        "status": "Online"
    }
    return render(request, "finance_dashboard/home.html", context)

def analysis(request):
    pair = request.GET.get('pair', 'EURUSD')
    return render(request, "finance_dashboard/analysis.html", {"selected_pair": pair})

def analysis_ajax(request):
    return JsonResponse({"success": True})

def portfolio(request):
    portfolios = Portfolio.objects.all()
    return render(request, "finance_dashboard/portfolio.html", {"portfolios": portfolios})

def insights(request):
    insights_qs = Insight.objects.all().order_by('-date')
    page = Paginator(insights_qs, 6).get_page(request.GET.get('page'))
    return render(request, "finance_dashboard/insights.html", {"page_obj": page})

def details(request, symbol=None):
    return render(request, "finance_dashboard/details.html", {"symbol": symbol})

def about(request):
    return render(request, "finance_dashboard/about.html")



# ====================== TRADES FILTER & SEARCH ====================

def filter_trades(request, trade_type=None):
    """ Lọc trades theo loại: Live / Backtest / All """
    trades = Trade.objects.all().order_by("-open_date")
    if trade_type in ["Live", "Backtest"]:
        trades = trades.filter(trade_type=trade_type)
    return render(request, "finance_dashboard/partials/trade_table.html", {"trades": trades})

def get_real_search_data(symbol, symbol_type='forex'):
    """ Thu thập dữ liệu thực tế từ yfinance """
    try:
        import yfinance as yf
        yf_symbol = symbol + '=X' if symbol_type == 'forex' and not symbol.endswith('=X') else symbol
        ticker = yf.Ticker(yf_symbol)
        hist = ticker.history(period="5d", interval="1d")
        if not hist.empty:
            last = float(hist["Close"].iloc[-1])
            prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else last
            change = round(((last - prev) / prev) * 100, 2) if prev else 0
            history = hist["Close"].astype(float).tolist()[-5:]
            avg_volume = hist["Volume"].mean() if "Volume" in hist.columns else 0
            volume = 'High' if avg_volume > 1000000 else 'Medium' if avg_volume > 100000 else 'Low'
            return {
                'last': round(last, 4 if symbol_type == 'forex' else 2),
                'change': change, 'history': history, 'volume': volume
            }
    except Exception as e:
        logger.warning(f"Search data error for {symbol}: {e}")
    return {'last': 0.0, 'change': 0.0, 'history': [0.0] * 5, 'volume': 'N/A'}

def search_view(request):
    """ Xử lý tìm kiếm Forex và Cổ phiếu """
    query = request.GET.get('query', '').upper()
    forex_symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD']
    stock_symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'NVDA', 'META']
    results = []
    if query:
        for s in forex_symbols:
            if query in s: results.append({'pair': s, 'data': get_real_search_data(s, 'forex'), 'type': 'Forex'})
        for s in stock_symbols:
            if query in s: results.append({'pair': s, 'data': get_real_search_data(s, 'stock'), 'type': 'Stock'})
    html = render_to_string('finance_dashboard/search_results.html', {'results': results, 'query': query})
    return HttpResponse(html)

def get_real_chart_data(symbol):
    """ Trích xuất dữ liệu biểu đồ cho Terminal """
    try:
        import yfinance as yf
        is_forex = any(f in symbol for f in ['EUR', 'GBP', 'JPY', 'USD'])
        yf_symbol = symbol + '=X' if is_forex and not symbol.endswith('=X') else symbol
        ticker = yf.Ticker(yf_symbol)
        hist = ticker.history(period="30d", interval="1d")
        if not hist.empty:
            return {
                'chart_data': {
                    'labels': [d.strftime("%Y-%m-%d") for d in hist.index],
                    'values': hist["Close"].astype(float).tolist(),
                    'high': round(float(hist["High"].max()), 4 if is_forex else 2),
                    'low': round(float(hist["Low"].min()), 4 if is_forex else 2),
                },
                'details': {
                    'last': round(float(hist["Close"].iloc[-1]), 4 if is_forex else 2),
                    'change': 0, 'history': hist["Close"].tolist()[-5:]
                }
            }
    except Exception as e:
        logger.warning(f"Chart error for {symbol}: {e}")
    return None

def chart_view(request, symbol):
    """ Render fragment biểu đồ """
    data = get_real_chart_data(symbol)
    if not data: return HttpResponse('<div class="alert alert-danger">Chart not available.</div>')
    return render(request, 'finance_dashboard/chart_fragment.html', {'symbol': symbol, **data})

@login_required
def edit_trade(request, trade_id):
    """ Chỉnh sửa thông số lệnh (SL/TP/Lot) """
    trade = get_object_or_404(Trade, id=trade_id)
    if request.method == "POST":
        try:
            trade.amount = request.POST.get('amount')
            trade.side = request.POST.get('side')
            trade.status = request.POST.get('status', 'OPEN')
            trade.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return redirect('portfolio')

@login_required
def delete_trade(request, trade_id):
    """ Tiêu hủy vị thế giao dịch """
    if request.method == "POST":
        get_object_or_404(Trade, id=trade_id).delete()
    return redirect('portfolio')

# ==========================================
# INSTITUTIONAL API ENDPOINTS (AUM TERMINAL)
# ==========================================

def clean_to_dict(val):
    """ Máy xay JSON: Lột sạch vỏ rác rưởi từ Frontend """
    if not val: return {}
    if isinstance(val, (dict, list)): return val
    try:
        return json.loads(val)
    except:
        return {"notes": str(val)}

@csrf_exempt
def aum_overview_api(request):
    """ CỔNG 1: TỔNG QUAN TÀI SẢN (OVERVIEW) """
    account = QuantAccount.objects.first()
    if not account: return JsonResponse({"error": "Account missing"}, status=404)
    exp = CentralRiskEngine.get_total_notional_exposure()
    return JsonResponse({
        "balance": account.balance, "equity": account.equity,
        "exposure": exp, "status": account.status
    })

@csrf_exempt
def exposure_radar_api(request):
    """ CỔNG 2: RADAR RỦI RO (EXPOSURE) """
    active = AlphaSignal.objects.filter(status__in=['EXECUTED', 'APPROVED', 'PENDING_EXEC'])
    radar = [{"symbol": s.ticker, "percent": 10.0} for s in active]
    return JsonResponse({"radar_scan": radar})

@csrf_exempt
def account_psyche_api(request):
    """ CỔNG 3: PHÂN TÂM HỌC (BEHAVIOR) """
    # Móc vào engine tâm lý sếp đã đúc
    from .risk_engine import BehavioralEngine
    regime, penalty, oci = BehavioralEngine.analyze_trader_psyche()
    return JsonResponse({"nodes": [{"regime": regime, "oci": oci}]})

@csrf_exempt
def ceo_action_api(request):
    """ CỔNG 4: NÚT ĐỎ QUYỀN LỰC (ACTION) """
    if request.method != "POST": return JsonResponse({"error": "POST ONLY"}, status=405)
    action = json.loads(request.body).get("action")
    if action == "FORCE_CLOSE":
        AlphaSignal.objects.filter(status='EXECUTED').update(status='PENDING_CLOSE')
    return JsonResponse({"message": "Directive executed."})

# ==========================================
# LÕI THỰC THI (MT5 BRIDGE)
# ==========================================

@csrf_exempt
def mt5_execution_node(request):
    """ Tiếp nhận tờ trình từ MT5 và soi rủi ro Kelly """
    if request.method != 'POST': return JsonResponse({"error": "POST ONLY"}, status=405)
    payload = json.loads(request.body)
    approved_cap = KellyEngine.calculate_final_bullet(
        capital=float(payload.get("balance", 10000)), win_rate=0.5, rr_ratio=2.0
    )
    if approved_cap <= 0: return JsonResponse({"directive": "REJECTED"})
    sig = AlphaSignal.objects.create(ticker=payload.get("ticker"), status='PENDING')
    return JsonResponse({"directive": "RECEIVED", "uuid": str(sig.uuid)})

@csrf_exempt
def close_trade_api(request):
    """ Lệnh rút quân khẩn cấp từ Web UI xuống MT5 """
    if request.method == 'POST':
        ticker = json.loads(request.body).get('ticker')
        AlphaSignal.objects.filter(ticker=ticker, status='EXECUTED').update(status='PENDING_CLOSE')
        return JsonResponse({"message": "Retreat order sent."})
    return JsonResponse({"error": "POST ONLY"}, status=405)

# ==========================================
# DI SẢN & ĐÁNH GIÁ (LEGACY & REVIEWS)
# ==========================================

@csrf_exempt
def review_api(request):
    """ Đóng sổ cái tuần (Weekly Review) """
    if request.method == "POST":
        data = json.loads(request.body)
        WeeklyReview.objects.update_or_create(week_start_date=data["week_start_date"])
        return JsonResponse({"status": "saved"})
    return JsonResponse({"status": "ready"})

@csrf_exempt
def config_state_api(request):
    """ Cổng nhận lệnh bơm tiền và cấu hình từ CEO """
    return JsonResponse({"status": "Legacy Port Active"})

@csrf_exempt
def dashboard_metrics_api(request):
    """ Bơm số liệu cho dashboard cũ không bị gãy """
    return JsonResponse({"balance": 100000, "status": "Stable"})

@csrf_exempt
def radar_blip_api(request):
    """ Nhận tín hiệu radar trinh sát từ MT5 """
    if request.method == 'POST':
        data = json.loads(request.body)
        RadarBlip.objects.update_or_create(symbol=data.get('symbol'))
        return JsonResponse({"message": "Radar locked"})
    return JsonResponse({"error": "POST ONLY"}, status=405)

@csrf_exempt
def mt5_direct_fire_api(request):
    """
    TÂM ĐIỂM HỎA LỰC: Nơi bóp cò lệnh và tính toán độ 'ngáo' (OCI)
    """
    if request.method != 'POST': 
        return JsonResponse({"error": "POST ONLY"}, status=405)
        
    try:
        data = json.loads(request.body)
        ticker = data.get('ticker')
        direction = data.get('direction')
        volume = data.get('volume')
        account_id = data.get('account_id', 1) # Mặc định là tài khoản 1 nếu thiếu

        # --- ĐOẠN NÀY LÀ KHÚC 'ĐIỆN ẢNH' ---
        # 1. Bắn lệnh sang MT5 (Giả lập hoặc gọi logic MT5 của sếp)
        # res_mt5 = call_mt5_logic(ticker, direction, volume) 
        
        # 2. Ngay khi lệnh 'vút bay', chúng ta tính điểm OCI ngay lập tức 
        new_oci = process_oci_impact(account_id, volume)
        
        logger.info(f"🚀 FIRE: {direction} {volume} Lots {ticker}. New OCI: {new_oci}")
        
        return JsonResponse({
            "status": "EXECUTED",
            "oci_index": new_oci,
            "message": "LÍNH ĐÁNH THUÊ MT5 ĐANG LÊN ĐẠN!"
        })
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
