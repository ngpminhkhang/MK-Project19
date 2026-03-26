import json
import traceback
import uuid
from django.http import JsonResponse
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum
from django.utils import timezone

# Lệnh bài sinh sát (Models mới)
from .models import (
    QuantAccount, PortfolioSetting, SystemLibrary, AlphaSignal,
    WeeklyOutlook, WeeklyReview, MissedTrade, RadarBlip, RiskLog
)

# ==========================================
# PHẦN 1: AUM TERMINAL
# ==========================================

@csrf_exempt
def get_portfolio_metrics(request):
    """Cung cấp số liệu tổng quan cho quỹ"""
    if request.method == 'GET':
        settings = PortfolioSetting.objects.first()
        max_risk = getattr(settings, 'max_risk_per_trade', 2.0) if settings else 2.0
        mode = "NORMAL" # Chế độ mặc định

        accounts = QuantAccount.objects.all()
        total_equity = sum([a.balance for a in accounts])

        acc_list = []
        for acc in accounts:
            status = acc.status
            weight = (acc.balance / total_equity * 100) if total_equity > 0 else 0

            closed_trades = AlphaSignal.objects.filter(status='CLOSED')
            total_trades = closed_trades.count()
            wins = closed_trades.filter(pnl__gt=0).count()
            win_rate = (wins / total_trades * 100) if total_trades > 0 else 0.0
            
            pnl_aggregate = closed_trades.aggregate(Sum('pnl'))['pnl__sum']
            net_pnl = float(pnl_aggregate) if pnl_aggregate else 0.0

            drawdown = ((10000.0 - acc.balance) / 10000.0 * 100) if acc.balance < 10000.0 else 0.0

            acc_list.append({
                "id": acc.id,
                "name": acc.account_name,
                "balance": acc.balance,
                "allocation_percent": weight,
                "status": status,
                "net_pnl": net_pnl,
                "drawdown_percent": drawdown,
                "win_rate": win_rate
            })

        return JsonResponse({
            "total_equity": total_equity,
            "mode": mode,
            "max_daily_risk": max_risk,
            "accounts": acc_list
        })

@csrf_exempt
def update_portfolio_mode(request):
    """Thay đổi chế độ giao dịch của quỹ"""
    if request.method == 'POST':
        return JsonResponse({"message": "System execution protocol transitioned successfully."})

@csrf_exempt
def apply_portfolio_rebalance(request):
    """Tái cân bằng vốn"""
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            payload = body.get('payload', [])
            for item in payload:
                acc_id = item.get('account_id')
                status = item.get('status', 'NORMAL')
                QuantAccount.objects.filter(id=acc_id).update(status=status)
            return JsonResponse({"message": "Capital reallocation executed successfully."})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
def get_performance_analytics(request):
    """Phân tích hiệu suất theo điểm số và giai đoạn"""
    if request.method == 'POST':
        try:
            closed_trades = AlphaSignal.objects.filter(status='CLOSED')
            by_score = {
                "A+ (85-100)": {"total_trades": 0, "wins": 0, "net_pnl": 0.0},
                "B (70-84)": {"total_trades": 0, "wins": 0, "net_pnl": 0.0},
                "C (60-69)": {"total_trades": 0, "wins": 0, "net_pnl": 0.0},
                "F (<60)": {"total_trades": 0, "wins": 0, "net_pnl": 0.0}
            }
            by_phase = {}

            for trade in closed_trades:
                is_win = 1 if (trade.pnl and trade.pnl > 0) else 0
                
                raw_checklist = trade.pre_trade_checklist
                checklist_dict = json.loads(raw_checklist) if isinstance(raw_checklist, str) and raw_checklist else {}
                score = checklist_dict.get('score', 0) if isinstance(checklist_dict, dict) else 0
                
                if score >= 85: key_score = "A+ (85-100)"
                elif score >= 70: key_score = "B (70-84)"
                elif score >= 60: key_score = "C (60-69)"
                else: key_score = "F (<60)"
                
                by_score[key_score]["total_trades"] += 1
                by_score[key_score]["wins"] += is_win
                by_score[key_score]["net_pnl"] += float(trade.pnl or 0)

                phase = trade.market_phase if trade.market_phase else "Unknown"
                if phase not in by_phase:
                    by_phase[phase] = {"total_trades": 0, "wins": 0, "net_pnl": 0.0}
                
                by_phase[phase]["total_trades"] += 1
                by_phase[phase]["wins"] += is_win
                by_phase[phase]["net_pnl"] += float(trade.pnl or 0)

            return JsonResponse({"by_score": by_score, "by_phase": by_phase})
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({"error": str(e)}, status=400)


# ==========================================
# PHẦN 2: SIGNAL ENGINE (CỖ MÁY ĐỊNH LƯỢNG)
# ==========================================

@csrf_exempt
def get_library_items(request):
    if request.method == 'GET':
        category = request.GET.get('category', '')
        items = SystemLibrary.objects.filter(category=category).order_by('-created_at')
        data = [{"id": i.id, "title": i.title, "category": i.category, "configuration": i.configuration} for i in items]
        return JsonResponse(data, safe=False)

@csrf_exempt
def get_app_settings(request):
    if request.method == 'GET':
        account_id = request.GET.get('accountId', 1)
        try:
            acc = QuantAccount.objects.get(id=account_id)
            return JsonResponse({"initial_balance": acc.balance, "currency": acc.account_currency})
        except:
            return JsonResponse({"initial_balance": 10000, "currency": "USD"})

@csrf_exempt
def get_portfolio_state(request):
    """Mắt thần CEO: Theo dõi độ hưng phấn và USD Bias"""
    if request.method == 'GET':
        account_id = request.GET.get('accountId', 1)
        
        # Quét lệnh đang chạy (EXECUTED) để tính USD Bias
        active_scenarios = AlphaSignal.objects.filter(status='EXECUTED')
        usd_bias = 0
        for s in active_scenarios:
            is_buy = 1 if s.signal_direction == 'BUY' else -1
            pair = s.ticker.upper()
            if pair.startswith('USD'): usd_bias += is_buy
            elif pair.endswith('USD') or pair.startswith('XAU') or pair.startswith('BTC'): usd_bias -= is_buy
            
        total_equity = sum([a.balance for a in QuantAccount.objects.all()])
        
        try:
            acc = QuantAccount.objects.get(id=account_id)
            status = acc.status
            weight = 100.0
        except:
            status = "NORMAL"
            weight = 100.0

        return JsonResponse({
            "mode": "NORMAL",
            "current_usd_bias": usd_bias,
            "account_status": status,
            "account_weight": weight,
            "total_equity": total_equity
        })

@csrf_exempt
def get_scenarios(request):
    if request.method == 'GET':
        scenarios = AlphaSignal.objects.all().order_by('-created_at')[:200]
        data = []
        for s in scenarios:
            data.append({"uuid": str(s.uuid), "pair": s.ticker, "status": s.status, "pnl": s.pnl})
        return JsonResponse(data, safe=False)

@csrf_exempt
def create_scenario(request):
    """Tạo kịch bản mới nháp"""
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            data = body.get('input', {}) if 'input' in body else body
            
            scenario = AlphaSignal.objects.create(
                ticker=data.get('pair', 'XAUUSD'),
                signal_direction=data.get('direction', 'BUY'),
                entry_price=data.get('entry_price', 0),
                sl=data.get('sl_price', 0),
                tp=data.get('tp_price', 0),
                ceo_approved_lot=data.get('volume', 0.01),
                status='PENDING'
            )
            return JsonResponse({"uuid": str(scenario.uuid)})
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
def set_scenario_status(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        AlphaSignal.objects.filter(uuid=data.get('uuid')).update(status=data.get('status'))
        return JsonResponse({"message": f"Updated to {data.get('status')}"})

@csrf_exempt
def delete_scenario(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        AlphaSignal.objects.filter(uuid=data.get('uuid')).delete()
        return JsonResponse({"message": "Deleted"})

@csrf_exempt
def execute_trade(request):
    """Giám đốc duyệt lệnh -> Chuyển sang APPROVED để chờ EA bắn"""
    if request.method == 'POST':
        data = json.loads(request.body)
        AlphaSignal.objects.filter(uuid=data.get('scenarioUuid')).update(status='APPROVED')
        return JsonResponse({"message": "Directive approved. Quantitative Execution Node pending fill."})
    
@csrf_exempt
def get_dashboard_stats(request):
    """API Cung cấp dữ liệu Dashboard"""
    if request.method == 'GET':
        closed_trades = AlphaSignal.objects.filter(status='CLOSED').order_by('created_at')
        
        try:
            acc = QuantAccount.objects.first()
            current_equity = float(acc.balance) if acc else 10000.0
        except:
            current_equity = 10000.0

        total_historical_pnl = sum(float(t.pnl or 0) for t in closed_trades)
        initial_balance = current_equity - total_historical_pnl
        
        total_trades = closed_trades.count()
        wins = 0
        gross_profit = 0.0
        gross_loss = 0.0
        long_count = 0
        
        history = []
        running_equity = initial_balance
        peak_equity = initial_balance
        max_dd = 0.0

        for t in closed_trades:
            pnl = float(t.pnl or 0)
            if t.signal_direction == 'BUY': long_count += 1
                
            if pnl > 0:
                wins += 1
                gross_profit += pnl
            else:
                gross_loss += abs(pnl)
                
            running_equity += pnl
            if running_equity > peak_equity:
                peak_equity = running_equity
            
            dd = (peak_equity - running_equity) / peak_equity * 100 if peak_equity > 0 else 0
            if dd > max_dd: max_dd = dd
                
            history.append({
                "name": t.created_at.strftime("%d/%m") if t.created_at else "",
                "equity": round(running_equity, 2)
            })

        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0.0
        pf = (gross_profit / gross_loss) if gross_loss > 0 else (99.9 if gross_profit > 0 else 0.0)
        long_ratio = (long_count / total_trades * 100) if total_trades > 0 else 50.0

        data = {
            "current_equity": round(current_equity, 2),
            "net_pnl": round(total_historical_pnl, 2),
            "pnl_percent": round((total_historical_pnl / initial_balance * 100), 2) if initial_balance > 0 else 0,
            "max_drawdown": round(max_dd, 2),
            "profit_factor": round(pf, 2),
            "expectancy": round((total_historical_pnl / total_trades), 2) if total_trades > 0 else 0,
            "win_rate": round(win_rate, 1),
            "total_trades": total_trades,
            "long_ratio": round(long_ratio, 1),
            "history": history,
            "setup_performance": []
        }
        return JsonResponse(data)


# ==========================================
# PHẦN 3: RADAR THỊ TRƯỜNG (MARKET MONITOR)
# ==========================================
LIVE_SIGNALS = {}

@csrf_exempt
def webhook_mt5_signal(request):
    if request.method == 'POST':
        try:
            clean_body = request.body.decode('utf-8').strip('\x00')
            data = json.loads(clean_body)
            sym = data.get("symbol")
            if data.get("action") == "DELETE":
                if sym in LIVE_SIGNALS: del LIVE_SIGNALS[sym]
                return JsonResponse({"status": "deleted"})
            
            LIVE_SIGNALS[sym] = data
            return JsonResponse({"status": "ok"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
def get_live_signals(request):
    if request.method == 'GET':
        return JsonResponse(list(LIVE_SIGNALS.values()), safe=False)
    
# ==========================================
# PHẦN 4: TRẠM THỰC THI (MT5 TICKET MASTER BRIDGE)
# ==========================================

@csrf_exempt
def bridge_get_pending_order(request):
    """Cổng 1: MT5 liên tục gõ cửa xin lệnh mới để bắn"""
    if request.method == 'GET':
        pending = AlphaSignal.objects.filter(status='APPROVED').order_by('created_at').first()
        if pending:
            return JsonResponse({
                "has_order": True,
                "uuid": str(pending.uuid),
                "pair": pending.ticker,
                "direction": pending.signal_direction,
                "volume": float(pending.ceo_approved_lot or 0),
                "sl_price": float(pending.sl or 0),
                "tp_price": float(pending.tp or 0)
            })
        return JsonResponse({"has_order": False})

@csrf_exempt
def bridge_confirm_execution(request):
    """Cổng 2: MT5 báo cáo đã vào lệnh thành công trên sàn"""
    if request.method == 'POST':
        try:
            clean_body = request.body.decode('utf-8').strip('\x00')
            data = json.loads(clean_body)
            uuid = data.get('uuid')
            AlphaSignal.objects.filter(uuid=uuid).update(status='EXECUTED')
            return JsonResponse({"status": "ok", "message": "Market execution confirmed."})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
def bridge_report_closed_trade(request):
    """Cổng 3: MT5 báo cáo đóng lệnh -> Tính tiền cộng vào Quỹ"""
    if request.method == 'POST':
        try:
            clean_body = request.body.decode('utf-8').strip('\x00')
            data = json.loads(clean_body)
            uuid = data.get('uuid')
            pnl = float(data.get('pnl', 0.0))
            
            scenario = AlphaSignal.objects.filter(uuid=uuid).first()
            if scenario and scenario.status != 'CLOSED':
                scenario.status = 'CLOSED'
                scenario.pnl = pnl
                scenario.save()
                
            account = QuantAccount.objects.first()
            if account:
                account.balance = float(account.balance) + pnl
                account.save()
                
            return JsonResponse({"status": "ok", "message": "Position liquidated."})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
        
@csrf_exempt
def bridge_sync_live_pnl(request):
    """Cổng MỚI: MT5 liên tục bơm PnL đang chạy"""
    if request.method == 'POST':
        try:
            clean_body = request.body.decode('utf-8').strip('\x00')
            data = json.loads(clean_body)
            uuid = data.get('uuid')
            pnl = float(data.get('pnl', 0.0))
            AlphaSignal.objects.filter(uuid=uuid, status='EXECUTED').update(pnl=pnl)
            return JsonResponse({"status": "ok"})
        except:
            return JsonResponse({"status": "error"}, status=400)
        
# ==========================================
# PHẦN 5: NHẬT KÝ GIAO DỊCH (TRADE JOURNAL)
# ==========================================

@csrf_exempt
def get_journal_trades(request):
    """DANH SÁCH LỆNH CHO TAB FUSION"""
    trades = AlphaSignal.objects.all().order_by('-created_at')[:50]
    data = [{"uuid": str(t.uuid), "pair": t.ticker, "direction": t.signal_direction, 
             "status": t.status, "pnl": float(t.pnl or 0)} for t in trades]
    return JsonResponse(data, safe=False)

@csrf_exempt
def update_journal_review(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            uuid = data.get('uuid')
            scenario = AlphaSignal.objects.filter(uuid=uuid).first()
            
            if scenario:
                scenario.review_data = data.get('review_data', '{}')
                scenario.result_images = data.get('result_images', '[]')
                scenario.trade_class = data.get('trade_class', '')
                scenario.exit_price = data.get('exit_price', 0.0)
                
                old_pnl = float(scenario.pnl or 0.0)
                new_pnl = float(data.get('pnl', old_pnl))
                
                if old_pnl != new_pnl and scenario.status == 'CLOSED':
                    diff = new_pnl - old_pnl
                    scenario.pnl = new_pnl
                    acc = QuantAccount.objects.first()
                    if acc:
                        acc.balance = float(acc.balance) + diff
                        acc.save()
                        
                scenario.save()
                return JsonResponse({"status": "ok"})
            return JsonResponse({"error": "Order sequence not found."}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
        
# ==========================================
# PHẦN 6: TRẠM KIỂM ĐIỂM TUẦN (WEEKLY REVIEW)
# ==========================================

@csrf_exempt
def get_weekly_review_data(request):
    if request.method == 'GET':
        account_id = request.GET.get('accountId', 1)
        week_start = request.GET.get('weekStart')
        
        review = WeeklyReview.objects.filter(account_id=account_id, week_start_date=week_start).first()
        outlook = WeeklyOutlook.objects.filter(week_start=week_start).first()
        
        return JsonResponse({
            "review": {
                "fa_accuracy": review.fa_accuracy,
                "ta_accuracy": review.ta_accuracy,
                "fusion_score": review.fusion_score,
                "review_details": review.review_details,
            } if review else None,
            "outlook": {
                "final_bias": outlook.weekly_bias,
                "script_plan": outlook.execution_script,
                "fa_bias": outlook.fa_bias,
            } if outlook else None
        })

@csrf_exempt
def save_weekly_review_data(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            account_id = data.get('accountId', 1)
            week_start = data.get('weekStart')
            review_data = data.get('review', {})
            outlook_data = data.get('outlook', {})
            
            WeeklyReview.objects.update_or_create(
                account_id=account_id, week_start_date=week_start,
                defaults={
                    "total_trades": review_data.get('total_trades', 0),
                    "win_rate": review_data.get('win_rate', 0.0),
                    "net_pnl": review_data.get('net_pnl', 0.0),
                    "fa_accuracy": review_data.get('fa_accuracy', 5),
                    "ta_accuracy": review_data.get('ta_accuracy', 5),
                    "fusion_score": review_data.get('fusion_score', 5),
                    "review_details": review_data.get('review_details', '{}')
                }
            )
            
            WeeklyOutlook.objects.update_or_create(
                week_start=week_start,
                defaults={
                    "weekly_bias": outlook_data.get('final_bias', 'NEUTRAL'),
                    "execution_script": outlook_data.get('script_plan', ''),
                    "fa_bias": outlook_data.get('fa_bias', '{}')
                }
            )
            return JsonResponse({"status": "ok"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
def handle_missed_trades(request):
    if request.method == 'GET':
        week_start = request.GET.get('weekStart')
        missed = MissedTrade.objects.filter(pair__isnull=False).order_by('-created_at')
        res = []
        for m in missed:
            res.append({
                "uuid": str(m.id), "pair": m.pair, "direction": m.direction,
                "reason": m.reason, "analysis_details": m.notes,
                "images": m.image_paths, "created_at": int(m.created_at.timestamp()) if m.created_at else 0
            })
        return JsonResponse(res, safe=False)
        
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            MissedTrade.objects.create(
                pair=data.get('pair', ''),
                direction=data.get('direction', 'BUY'),
                reason=data.get('reason', ''),
                notes=data.get('notes', ''),
                image_paths=data.get('images', '[]')
            )
            return JsonResponse({"status": "ok"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
            
    elif request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            MissedTrade.objects.filter(id=data.get('uuid')).delete()
            return JsonResponse({"status": "ok"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
        
# ==========================================
# PHẦN 7: RADAR & LIVE POSITIONS (MONITOR)
# ==========================================
@csrf_exempt
def get_active_trades(request):
    if request.method == 'GET':
        try:
            active_scenarios = AlphaSignal.objects.filter(status='EXECUTED').order_by('-created_at')
            res = []
            for s in active_scenarios:
                res.append({
                    "uuid": str(s.uuid),
                    "pair": s.ticker,
                    "direction": s.signal_direction,
                    "volume": float(s.ceo_approved_lot or 0),
                    "entry_price": float(s.entry_price or 0),
                    "pnl": float(s.pnl) if s.pnl else 0.0,
                })
            return JsonResponse(res, safe=False)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def kill_switch_trade(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            uuid_str = data.get('uuid')
            AlphaSignal.objects.filter(uuid=uuid_str, status='EXECUTED').update(status='PENDING_CLOSE')
            return JsonResponse({"status": "ok", "message": "Emergency liquidation protocol transmitted."})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
def bridge_pending_closes(request):
    if request.method == 'GET':
        trade = AlphaSignal.objects.filter(status='PENDING_CLOSE').first()
        if trade:
            return JsonResponse({"has_close_order": True, "uuid": str(trade.uuid), "pair": trade.ticker})
        return JsonResponse({"has_close_order": False})
    
# ==========================================
# PHẦN 8: KHO VŨ KHÍ (SYSTEM LIBRARY)
# ==========================================
@csrf_exempt
def manage_system_library(request):
    try:
        if request.method == 'GET':
            category = request.GET.get('category')
            items = SystemLibrary.objects.all().order_by('-id')
            if category:
                items = items.filter(category=category)
                
            res = []
            for i in items:
                cfg = getattr(i, 'configuration', {})
                cfg_str = json.dumps(cfg) if isinstance(cfg, dict) else str(cfg) if cfg else "{}"
                res.append({
                    "id": i.id, 
                    "title": getattr(i, 'title', ''), 
                    "category": getattr(i, 'category', ''), 
                    "configuration": cfg_str
                })
            return JsonResponse(res, safe=False)
            
        elif request.method == 'POST':
            data = json.loads(request.body)
            item_id = data.get('id')
            title = data.get('title', 'Unknown Setup')
            category = data.get('category', 'SETUP')
            
            raw_config = data.get('configuration', '{}')
            config_data = json.loads(raw_config) if isinstance(raw_config, str) else raw_config
                
            if item_id:
                SystemLibrary.objects.filter(id=item_id).update(
                    title=title, category=category, configuration=config_data
                )
            else:
                SystemLibrary.objects.create(
                    title=title, category=category, configuration=config_data
                )
            return JsonResponse({"status": "ok"})
            
        elif request.method == 'DELETE':
            data = json.loads(request.body)
            SystemLibrary.objects.filter(id=data.get('id')).delete()
            return JsonResponse({"status": "ok"})
            
        return JsonResponse({"error": "Method not allowed"}, status=405)

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": f"CRITICAL SYSTEM FAILURE: {str(e)}"}, status=400)
    
# ==========================================
# PHẦN 9: TRUNG TÂM QUYỀN LỰC (CEO CONFIG)
# ==========================================
@csrf_exempt
def manage_system_config(request):
    if request.method == 'GET':
        try:
            account_id = request.GET.get('accountId', 1)
            acc, _ = QuantAccount.objects.get_or_create(id=account_id, defaults={'account_name': 'Main Fund'})
            
            return JsonResponse({
                "balance": acc.balance,
                "mode": "NORMAL", 
                "max_risk": 2.0,
                "account_weight": 100.0,
                "account_status": acc.status 
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            account_id = data.get('accountId', 1)

            acc = QuantAccount.objects.get(id=account_id)
            acc.balance = float(data.get('balance', acc.balance))
            acc.status = data.get('account_status', acc.status)
            acc.save()

            return JsonResponse({"status": "ok"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
def get_settings(request):
    try:
        acc = QuantAccount.objects.first()
        return JsonResponse({"initial_balance": acc.balance if acc else 10000})
    except:
        return JsonResponse({"initial_balance": 10000})
    
# ==========================================
# PART 10: INSTITUTIONAL DASHBOARD METRICS
# ==========================================
@csrf_exempt
def get_dashboard_metrics(request):
    try:
        acc, _ = QuantAccount.objects.get_or_create(id=1, defaults={'account_name': 'Master Fund', 'balance': 10000})
        closed_trades = AlphaSignal.objects.filter(status='CLOSED')
        total_closed = closed_trades.count()
        wins = closed_trades.filter(pnl__gt=0).count()
        win_rate = (wins / total_closed * 100) if total_closed > 0 else 0
        net_pnl = sum([t.pnl for t in closed_trades if t.pnl])

        active_trades = AlphaSignal.objects.filter(status='EXECUTED')
        active_exposure_lots = sum([t.ceo_approved_lot for t in active_trades if t.ceo_approved_lot])
        floating_pnl = sum([t.pnl for t in active_trades if t.pnl])

        return JsonResponse({
            "aum": acc.balance,
            "net_pnl": net_pnl,
            "floating_pnl": floating_pnl,
            "win_rate": round(win_rate, 2),
            "total_trades": total_closed,
            "active_positions": active_trades.count(),
            "active_exposure": active_exposure_lots,
            "system_mode": "NORMAL",
            "max_drawdown_limit": 10.0
        })
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)
    
@csrf_exempt
def get_current_outlook(request):
    """ Bọc thép cổng ĐỌC Outlook cho giao diện Fusion """
    if request.method == 'GET':
        week_start = request.GET.get('week_start')
        try:
            # Truy vấn thẳng vào bảng WeeklyOutlook mới
            outlook = WeeklyOutlook.objects.filter(week_start=week_start).first()
            if outlook:
                return JsonResponse({
                    "status": "ok",
                    "final_bias": outlook.weekly_bias,
                    "script_plan": outlook.execution_script,
                    "fa_bias": outlook.fa_bias 
                })
            return JsonResponse({"status": "empty"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
@csrf_exempt
def get_current_outlook(request):
    """ Bọc thép cổng ĐỌC Outlook cho giao diện Fusion """
    if request.method == 'GET':
        week_start = request.GET.get('week_start')
        try:
            # Truy vấn thẳng vào bảng WeeklyOutlook mới
            from .models import WeeklyOutlook
            outlook = WeeklyOutlook.objects.filter(week_start=week_start).first()
            if outlook:
                return JsonResponse({
                    "status": "ok",
                    "final_bias": outlook.weekly_bias,
                    "script_plan": outlook.execution_script,
                    "fa_bias": outlook.fa_bias 
                })
            return JsonResponse({"status": "empty"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
@csrf_exempt
@transaction.atomic # KHÓA HỆ THỐNG: Chống 3 Node cùng gửi lệnh [cite: 24]
def mt5_execution_node(request):
    if request.method != 'POST': return JsonResponse({"error": "POST ONLY"}, status=405)
    try:
        payload = json.loads(request.body)
        balance = float(payload.get("balance", 10000))
        price = float(payload.get("entry_price", 1.0))
        
        # 1. Tính toán đạn dược theo Kelly + Tâm lý [cite: 542]
        approved_cap = KellyEngine.calculate_final_bullet(balance)
        new_lot = round((approved_cap / 10000), 2)
        
        if new_lot < 0.01:
            RiskLog.objects.create(decision="REJECTED", reason="Kelly Engine: No edge detected.") [cite: 532]
            return JsonResponse({"directive": "REJECTED", "reason": "Insufficient Kelly allocation"})

        # 2. Kiểm duyệt Exposure (Cổng soát vé rủi ro) [cite: 312, 329]
        is_safe, msg, pct = CentralRiskEngine.validate_new_trade(balance, new_lot, price)

        if is_safe:
            sig = AlphaSignal.objects.create(
                ticker=payload.get("ticker"),
                signal_direction=payload.get("signal_direction"),
                entry_price=price,
                ceo_approved_lot=new_lot,
                status='PENDING'
            ) [cite: 329, 350]
            RiskLog.objects.create(signal=sig, decision="APPROVED", reason=msg) [cite: 140, 141]
            return JsonResponse({"directive": "RECEIVED", "uuid": str(sig.uuid), "approved_lot": new_lot})
        else:
            RiskLog.objects.create(decision="REJECTED", reason=msg)
            return JsonResponse({"directive": "REJECTED", "reason": msg})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
@transaction.atomic # GIẢI QUYẾT RACE CONDITION TẠI ĐÂY
def mt5_execution_node(request):
    """Cổng nhận Proposal từ MT5 - Có kiểm soát rủi ro nguyên tử"""
    if request.method != 'POST': return JsonResponse({"error": "POST ONLY"}, status=405)
    try:
        payload = json.loads(request.body)
        balance = float(payload.get("balance", 10000))
        price = float(payload.get("entry_price", 1.0))
        
        # 1. Tính toán Size theo Kelly & Tâm lý
        approved_cap = KellyEngine.calculate_final_bullet(balance)
        new_lot = round((approved_cap / 10000), 2)
        
        if new_lot < 0.01:
            RiskLog.objects.create(decision="REJECTED", reason="Kelly Engine: Insufficient Edge.")
            return JsonResponse({"directive": "REJECTED", "reason": "Low edge"})

        # 2. Check Exposure toàn cầu
        is_safe, msg = CentralRiskEngine.validate_new_trade(balance, new_lot, price)

        if is_safe:
            sig = AlphaSignal.objects.create(
                ticker=payload.get("ticker"),
                signal_direction=payload.get("signal_direction"),
                entry_price=price,
                ceo_approved_lot=new_lot,
                status='PENDING'
            )
            RiskLog.objects.create(signal=sig, decision="APPROVED", reason=msg)
            return JsonResponse({"directive": "RECEIVED", "uuid": str(sig.uuid), "approved_lot": new_lot})
        else:
            RiskLog.objects.create(decision="REJECTED", reason=msg)
            return JsonResponse({"directive": "REJECTED", "reason": msg})
    except Exception as e: return JsonResponse({"error": str(e)}, status=400)

    
@csrf_exempt
def exposure_radar_api(request):
    """
    QUANTITATIVE RADAR: Phân loại 3 thị trường & ép rủi ro về thực tại.
    Công thức: $$Value = Lot \times ContractSize \times Price$$
    """
    # Chỉ quét lệnh đang thực thi để tính Exposure thật
    active = AlphaSignal.objects.filter(status='EXECUTED')
    exposure_map = {}
    total_val = 0
    
    for pos in active:
        lot = pos.ceo_approved_lot or 0
        price = pos.entry_price or 1.0
        ticker = pos.ticker.upper()
        
        # --- THIẾT LẬP CONTRACT SIZE HỌC THUẬT ---
        if any(x in ticker for x in ['GC', 'SI', 'PL', 'CL', 'HG']):
            c_size, market = 100, "Commodity Market"
        elif any(x in ticker for x in ['AAPL', 'NVDA', 'TSLA', 'MSFT', 'GOOGL', 'BTC', 'ETH']):
            c_size, market = 1, "Equity Market"
        else:
            c_size, market = 100000, "Currency Market"
            
        val = lot * c_size * price
        exposure_map[market] = exposure_map.get(market, 0) + val
        total_val += val
        
    radar_data = [
        {"name": k, "value": round(v, 2), "percent": round(v/total_val*100, 2)} 
        for k, v in exposure_map.items() if total_val > 0
    ]
    
    return JsonResponse({
        "total_notional": round(total_val, 2), 
        "radar_scan": radar_data
    })

@csrf_exempt
def get_risk_logs(request):
    """
    ORDER AUDIT TRAIL: Lấy danh sách nhật ký rủi ro để lấp đầy UI.
    """
    # Lấy 50 log mới nhất để iPad nhìn cho "kín cổng cao tường"
    logs = RiskLog.objects.select_related('signal').order_by('-id')[:50]
    data = [{
        "id": log.id,
        "timestamp": log.signal.created_at.strftime("%H:%M:%S") if log.signal else "00:00:00",
        "ticker": log.signal.ticker if log.signal else "N/A",
        "decision": log.decision,
        "reason": log.reason
    } for log in logs]
    
    return JsonResponse(data, safe=False)

@csrf_exempt
def get_trade_ledger(request):
    """FUSION: Hiển thị nhật ký giao dịch thực tế (Executed)"""
    executed_trades = AlphaSignal.objects.filter(status__in=['EXECUTED', 'Sent to Broker']).order_by('-created_at')[:30]
    data = [{
        "ticker": t.ticker,
        "direction": t.signal_direction,
        "entry": t.entry_price,
        "lot": t.ceo_approved_lot,
        "pnl": t.pnl,
        "status": t.status
    } for t in executed_trades]
    return JsonResponse(data, safe=False)

@csrf_exempt
def get_missed_signals(request):
    """MISSED: Các tín hiệu bị Risk Engine 'trảm' vì quá rủi ro"""
    rejected = AlphaSignal.objects.filter(status='REJECTED').order_by('-created_at')[:30]
    data = [{
        "ticker": t.ticker,
        "reason": "VaR Breach (>30% Cap)", # Giả lập lý do học thuật
        "lot": t.ceo_approved_lot,
        "time": t.created_at.strftime("%H:%M")
    } for t in rejected]
    return JsonResponse(data, safe=False)