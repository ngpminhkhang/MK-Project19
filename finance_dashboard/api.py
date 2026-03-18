import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum
from .models import QuantAccount, PortfolioSetting, AccountWeight, QuantScenario, SystemLibrary

# ==========================================
# PHẦN 1: AUM TERMINAL
# ==========================================

@csrf_exempt
def get_portfolio_metrics(request):
    if request.method == 'GET':
        settings = PortfolioSetting.objects.first()
        mode = settings.mode if settings else "NORMAL"
        max_risk = settings.max_daily_risk_percent if settings else 2.0

        accounts = QuantAccount.objects.all()
        total_equity = sum([a.balance for a in accounts])

        acc_list = []
        for acc in accounts:
            weight_obj = AccountWeight.objects.filter(account=acc).first()
            weight = weight_obj.weight_percent if weight_obj else (acc.balance / total_equity * 100 if total_equity > 0 else 0)
            status = weight_obj.status if weight_obj else "NORMAL"

            closed_trades = QuantScenario.objects.filter(account=acc, status='CLOSED')
            total_trades = closed_trades.count()
            wins = closed_trades.filter(pnl__gt=0).count()
            win_rate = (wins / total_trades * 100) if total_trades > 0 else 0.0
            
            pnl_aggregate = closed_trades.aggregate(Sum('pnl'))['pnl__sum']
            net_pnl = float(pnl_aggregate) if pnl_aggregate else 0.0

            drawdown = ((10000.0 - acc.balance) / 10000.0 * 100) if acc.balance < 10000.0 else 0.0

            acc_list.append({
                "id": acc.id,
                "name": acc.name,
                "balance": acc.balance,
                "allocation_percent": weight,
                "status": status,
                "net_pnl": net_pnl,
                "drawdown_percent": drawdown,
                "win_rate": win_rate
            })

        data = {
            "total_equity": total_equity,
            "mode": mode,
            "max_daily_risk": max_risk,
            "accounts": acc_list
        }
        return JsonResponse(data)

@csrf_exempt
def update_portfolio_mode(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            new_mode = body.get('mode', 'NORMAL')
            setting, created = PortfolioSetting.objects.get_or_create(id=1)
            setting.mode = new_mode
            setting.save()
            return JsonResponse({"message": f"System execution protocol transitioned to: {new_mode}"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
def apply_portfolio_rebalance(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            payload = body.get('payload', [])
            for item in payload:
                acc_id = item.get('account_id')
                weight = item.get('weight_percent', 0.0)
                status = item.get('status', 'NORMAL')
                account = QuantAccount.objects.get(id=acc_id)
                AccountWeight.objects.update_or_create(
                    account=account,
                    defaults={'weight_percent': weight, 'status': status}
                )
            return JsonResponse({"message": "Capital reallocation and portfolio rebalancing executed successfully."})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
def get_performance_analytics(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            account_id = body.get('accountId')
            closed_trades = QuantScenario.objects.filter(account_id=account_id, status='CLOSED')
            
            by_score = {
                "A+ (85-100)": {"total_trades": 0, "wins": 0, "net_pnl": 0.0},
                "B (70-84)": {"total_trades": 0, "wins": 0, "net_pnl": 0.0},
                "C (60-69)": {"total_trades": 0, "wins": 0, "net_pnl": 0.0},
                "F (<60)": {"total_trades": 0, "wins": 0, "net_pnl": 0.0}
            }
            by_phase = {}

            for trade in closed_trades:
                is_win = 1 if trade.pnl > 0 else 0
                score = trade.pre_trade_checklist.get('score', 0) if isinstance(trade.pre_trade_checklist, dict) else 0
                if score >= 85: key_score = "A+ (85-100)"
                elif score >= 70: key_score = "B (70-84)"
                elif score >= 60: key_score = "C (60-69)"
                else: key_score = "F (<60)"
                
                by_score[key_score]["total_trades"] += 1
                by_score[key_score]["wins"] += is_win
                by_score[key_score]["net_pnl"] += float(trade.pnl)

                phase = trade.market_phase if trade.market_phase else "Unknown"
                if phase not in by_phase:
                    by_phase[phase] = {"total_trades": 0, "wins": 0, "net_pnl": 0.0}
                
                by_phase[phase]["total_trades"] += 1
                by_phase[phase]["wins"] += is_win
                by_phase[phase]["net_pnl"] += float(trade.pnl)

            return JsonResponse({"by_score": by_score, "by_phase": by_phase})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


# ==========================================
# PHẦN 2: SIGNAL ENGINE (CỖ MÁY ĐỊNH LƯỢNG)
# ==========================================

@csrf_exempt
def get_library_items(request):
    """Lấy danh sách Setup, Risk Profile, Exit Strat từ Thư viện"""
    if request.method == 'GET':
        category = request.GET.get('category', '')
        items = SystemLibrary.objects.filter(category=category).order_by('-created_at')
        data = [{"id": i.id, "title": i.title, "content": i.content, "configuration": i.configuration} for i in items]
        return JsonResponse(data, safe=False)

@csrf_exempt
def get_app_settings(request):
    """Lấy vốn gốc của tài khoản để tính Risk"""
    if request.method == 'GET':
        account_id = request.GET.get('accountId')
        try:
            acc = QuantAccount.objects.get(id=account_id)
            return JsonResponse({"initial_balance": acc.balance, "currency": acc.currency})
        except:
            return JsonResponse({"initial_balance": 10000, "currency": "USD"})

@csrf_exempt
def get_portfolio_state(request):
    """Mắt thần CEO: Theo dõi độ hưng phấn và USD Bias"""
    if request.method == 'GET':
        account_id = request.GET.get('accountId')
        settings = PortfolioSetting.objects.first()
        mode = settings.mode if settings else "NORMAL"
        
        # Quét lệnh đang chạy để tính USD Bias
        active_scenarios = QuantScenario.objects.filter(status__in=['ACTIVE', 'FILLED'])
        usd_bias = 0
        for s in active_scenarios:
            is_buy = 1 if s.direction == 'BUY' else -1
            pair = s.pair.upper()
            if pair.startswith('USD'): usd_bias += is_buy
            elif pair.endswith('USD') or pair.startswith('XAU') or pair.startswith('BTC') or pair.startswith('US30') or pair.startswith('NAS'): usd_bias -= is_buy
            
        total_equity = sum([a.balance for a in QuantAccount.objects.all()])
        
        try:
            weight_obj = AccountWeight.objects.get(account_id=account_id)
            status = weight_obj.status
            weight = weight_obj.weight_percent
        except:
            status = "NORMAL"
            weight = 100.0

        return JsonResponse({
            "mode": mode,
            "current_usd_bias": usd_bias,
            "account_status": status,
            "account_weight": weight,
            "total_equity": total_equity
        })

@csrf_exempt
def get_scenarios(request):
    """Rút hồ sơ tất cả các lệnh đã lên kịch bản"""
    if request.method == 'GET':
        account_id = request.GET.get('accountId')
        scenarios = QuantScenario.objects.filter(account_id=account_id).order_by('-created_at')[:200]
        data = []
        for s in scenarios:
            data.append({
                "uuid": str(s.uuid), "pair": s.pair, "direction": s.direction, "status": s.status,
                "pnl": s.pnl, "entry_price": s.entry_price, "sl_price": s.sl_price, "tp_price": s.tp_price,
                "volume": s.volume, "setup_id": s.setup_id, "analysis_details": s.analysis_details,
                "pre_trade_checklist": s.pre_trade_checklist, "images": s.images, "result_images": s.result_images,
                "htf_trend": s.htf_trend, "market_phase": s.market_phase, "dealing_range": s.dealing_range,
                "narrative": s.narrative, "scenario_type": s.scenario_type
            })
        return JsonResponse(data, safe=False)

@csrf_exempt
def create_scenario(request):
    """Tạo kịch bản mới nháp"""
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            data = body.get('input', {}) if 'input' in body else body
            
            scenario = QuantScenario.objects.create(
                account_id=data.get('account_id', 1),
                pair=data.get('pair', 'XAUUSD'),
                direction=data.get('direction', 'BUY'),
                entry_price=data.get('entry_price', 0),
                sl_price=data.get('sl_price', 0),
                tp_price=data.get('tp_price', 0),
                volume=data.get('volume', 0.01),
                outlook_id=data.get('outlook_id', '')
            )
            return JsonResponse({"uuid": str(scenario.uuid)})
        except Exception as e:
            import traceback
            traceback.print_exc() # Ép nhổ lỗi chi tiết ra Terminal
            return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
def update_scenario_full(request):
    """Lưu toàn bộ phân tích, điểm số, và Risk profile"""
    if request.method == 'POST':
        body = json.loads(request.body)
        data = body.get('input', {}) if 'input' in body else body
        try:
            scenario = QuantScenario.objects.get(uuid=data.get('uuid'))
            scenario.analysis_details = data.get('analysis', '{}')
            scenario.pre_trade_checklist = data.get('checklist', '{}')
            scenario.risk_data = data.get('risk_data', '{}')
            scenario.images = data.get('images', '[]')
            scenario.setup_id = data.get('setup_id')
            scenario.entry_price = data.get('entry_price', 0)
            scenario.sl_price = data.get('sl_price', 0)
            scenario.tp_price = data.get('tp_price', 0)
            scenario.volume = data.get('volume', 0.01)
            scenario.htf_trend = data.get('htf_trend', '')
            scenario.market_phase = data.get('market_phase', '')
            scenario.dealing_range = data.get('dealing_range', '')
            scenario.narrative = data.get('narrative', '')
            scenario.scenario_type = data.get('scenario_type', '')
            scenario.save()
            return JsonResponse({"message": "Saved"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
def set_scenario_status(request):
    """Đánh dấu lệnh Missed, Cancelled"""
    if request.method == 'POST':
        data = json.loads(request.body)
        QuantScenario.objects.filter(uuid=data.get('uuid')).update(status=data.get('status'))
        return JsonResponse({"message": f"Updated to {data.get('status')}"})

@csrf_exempt
def delete_scenario(request):
    """Xóa sổ lệnh"""
    if request.method == 'POST':
        data = json.loads(request.body)
        QuantScenario.objects.filter(uuid=data.get('uuid')).delete()
        return JsonResponse({"message": "Deleted"})

@csrf_exempt
def execute_trade(request):
    """Gửi lệnh cho Trạm Bơm MT5"""
    if request.method == 'POST':
        data = json.loads(request.body)
        QuantScenario.objects.filter(uuid=data.get('scenarioUuid')).update(status='PENDING_EXEC')
        return JsonResponse({"message": "Directive approved. Quantitative Execution Node pending fill."})
    
@csrf_exempt
def get_dashboard_stats(request):
    """API Cung cấp dữ liệu Dashboard: Fix triệt để lỗi nhân đôi PnL"""
    if request.method == 'GET':
        account_id = request.GET.get('accountId', 1)
        closed_trades = QuantScenario.objects.filter(account_id=account_id, status='CLOSED').order_by('created_at')
        
        try:
            acc = QuantAccount.objects.get(id=account_id)
            # ĐÂY LÀ SỐ DƯ THỰC TẾ TRONG KHO (VD: 10003.10)
            current_equity = float(acc.balance)
        except:
            current_equity = 10000.0

        # TỔNG LỢI NHUẬN TỪ TRƯỚC TỚI NAY
        total_historical_pnl = sum(float(t.pnl) for t in closed_trades)
        
        # TÍNH NGƯỢC LẠI VỐN BAN ĐẦU ĐỂ VẼ BIỂU ĐỒ (VD: 10003.10 - 3.10 = 10000.0)
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
        setup_stats = {}

        for t in closed_trades:
            pnl = float(t.pnl)
            if t.direction == 'BUY': long_count += 1
                
            if pnl > 0:
                wins += 1
                gross_profit += pnl
            else:
                gross_loss += abs(pnl)
                
            # CHỈ CỘNG VÀO RUNNING_EQUITY ĐỂ VẼ BIỂU ĐỒ.
            # TUYỆT ĐỐI KHÔNG CỘNG VÀO CURRENT_EQUITY Ở ĐÂY NỮA!
            running_equity += pnl
            if running_equity > peak_equity:
                peak_equity = running_equity
            
            dd = (peak_equity - running_equity) / peak_equity * 100 if peak_equity > 0 else 0
            if dd > max_dd: max_dd = dd
                
            history.append({
                "name": t.created_at.strftime("%d/%m") if t.created_at else "",
                "equity": round(running_equity, 2)
            })
            
            setup_id = str(t.setup_id) if t.setup_id else "Unknown"
            if setup_id not in setup_stats:
                setup_stats[setup_id] = {"name": f"Model {setup_id}", "trades": 0, "wins": 0, "pnl": 0.0}
            setup_stats[setup_id]["trades"] += 1
            if pnl > 0: setup_stats[setup_id]["wins"] += 1
            setup_stats[setup_id]["pnl"] += pnl

        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0.0
        pf = (gross_profit / gross_loss) if gross_loss > 0 else (99.9 if gross_profit > 0 else 0.0)
        long_ratio = (long_count / total_trades * 100) if total_trades > 0 else 50.0
        
        setup_performance = [{"name": v["name"], "trades": v["trades"], "win_rate": round(v["wins"] / v["trades"] * 100, 1) if v["trades"] > 0 else 0, "pnl": round(v["pnl"], 2)} for k, v in setup_stats.items()]

        data = {
            "current_equity": round(current_equity, 2), # GỬI THẲNG SỐ DƯ 10003.10 RA MẶT TIỀN
            "net_pnl": round(total_historical_pnl, 2),
            "pnl_percent": round((total_historical_pnl / initial_balance * 100), 2) if initial_balance > 0 else 0,
            "max_drawdown": round(max_dd, 2),
            "profit_factor": round(pf, 2),
            "expectancy": round((total_historical_pnl / total_trades), 2) if total_trades > 0 else 0,
            "win_rate": round(win_rate, 1),
            "total_trades": total_trades,
            "long_ratio": round(long_ratio, 1),
            "history": history,
            "setup_performance": setup_performance
        }
        return JsonResponse(data)

# ==========================================
# PHẦN 3: RADAR THỊ TRƯỜNG (MARKET MONITOR)
# ==========================================
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

LIVE_SIGNALS = {}

@csrf_exempt
def webhook_mt5_signal(request):
    """Lỗ hổng để MT5 Universal Spy đút tín hiệu vào (Đã lắp bộ lọc rác \x00)"""
    if request.method == 'POST':
        try:
            # Lột sạch ký tự \x00 do MQL5 gửi dư thừa
            clean_body = request.body.decode('utf-8').strip('\x00')
            data = json.loads(clean_body)
            sym = data.get("symbol")
            
            # EA gửi lệnh xóa khi mất tín hiệu
            if data.get("action") == "DELETE":
                if sym in LIVE_SIGNALS:
                    del LIVE_SIGNALS[sym]
                return JsonResponse({"status": "deleted"})
            
            LIVE_SIGNALS[sym] = data
            return JsonResponse({"status": "ok"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
def get_live_signals(request):
    """Cổng xuất dữ liệu cho React Market Monitor hút"""
    if request.method == 'GET':
        return JsonResponse(list(LIVE_SIGNALS.values()), safe=False)
    
# ==========================================
# PHẦN 4: TRẠM THỰC THI (MT5 TICKET MASTER BRIDGE)
# ==========================================

@csrf_exempt
def bridge_get_pending_order(request):
    """Cổng 1: MT5 liên tục gõ cửa xin lệnh mới để bắn"""
    if request.method == 'GET':
        # Tìm lệnh nào CEO vừa duyệt xong (PENDING_EXEC)
        pending = QuantScenario.objects.filter(status='PENDING_EXEC').order_by('created_at').first()
        if pending:
            return JsonResponse({
                "has_order": True,
                "uuid": str(pending.uuid),
                "pair": pending.pair,
                "direction": pending.direction,
                "volume": float(pending.volume),
                "sl_price": float(pending.sl_price),
                "tp_price": float(pending.tp_price)
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
            QuantScenario.objects.filter(uuid=uuid).update(status='ACTIVE')
            return JsonResponse({"status": "ok", "message": "Market execution confirmed and mapped."})
        except Exception as e:
            import traceback
            traceback.print_exc()
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
            
            scenario = QuantScenario.objects.filter(uuid=uuid).first()
            if scenario and scenario.status != 'CLOSED':
                scenario.status = 'CLOSED'
                scenario.pnl = pnl
                scenario.save()
                
            account = QuantAccount.objects.filter(id=scenario.account_id).first()
            if account:
                account.balance = float(account.balance) + pnl
                account.save()
                
            return JsonResponse({"status": "ok", "message": "Position liquidated. Capital repatriated to Master Fund."})
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({"error": str(e)}, status=400)
        
@csrf_exempt
def bridge_sync_live_pnl(request):
    """Cổng MỚI: MT5 liên tục bơm PnL đang chạy (Floating PnL) lên Web"""
    if request.method == 'POST':
        try:
            clean_body = request.body.decode('utf-8').strip('\x00')
            data = json.loads(clean_body)
            uuid = data.get('uuid')
            pnl = float(data.get('pnl', 0.0))
            
            # Chỉ cập nhật PnL khi lệnh đang ACTIVE
            QuantScenario.objects.filter(uuid=uuid, status='ACTIVE').update(pnl=pnl)
            return JsonResponse({"status": "ok"})
        except:
            return JsonResponse({"status": "error"}, status=400)
        
# ==========================================
# PHẦN 5: NHẬT KÝ GIAO DỊCH (TRADE JOURNAL)
# ==========================================
from django.db.models import Q

@csrf_exempt
def get_journal_trades(request):
    """Lấy danh sách lịch sử lệnh (Đã lắp radar dò tên cột)"""
    if request.method == 'GET':
        try:
            account_id = request.GET.get('accountId', 1)
            outcome = request.GET.get('outcome', 'ALL')
            pair = request.GET.get('pair', '')

            trades = QuantScenario.objects.filter(account_id=account_id).exclude(status='PENDING_EXEC')
            if pair: trades = trades.filter(pair=pair)
            
            if outcome == 'WIN': trades = trades.filter(pnl__gt=0)
            elif outcome == 'LOSS': trades = trades.filter(pnl__lt=0)
            elif outcome == 'MISSED': trades = trades.filter(status__in=['MISSED', 'CANCELLED'])

            trades = trades.order_by('-created_at')
            results = []
            
            def safe_float(val):
                try: return float(val) if val else 0.0
                except: return 0.0

            for t in trades:
                analysis_dict = {}
                # Radar tự dò tên cột phân tích (analysis_details hoặc analysis)
                raw_analysis = getattr(t, 'analysis_details', getattr(t, 'analysis', "{}"))
                try:
                    if raw_analysis: analysis_dict = json.loads(raw_analysis)
                except: pass
                
                # Radar tự dò tên cột checklist
                checklist_data = getattr(t, 'checklist', getattr(t, 'pre_trade_checklist', "{}"))

                results.append({
                    "uuid": str(t.uuid),
                    "pair": getattr(t, 'pair', ""),
                    "direction": getattr(t, 'direction', "BUY"),
                    "status": getattr(t, 'status', "UNKNOWN"),
                    "pnl": safe_float(getattr(t, 'pnl', 0)),
                    "entry_price": safe_float(getattr(t, 'entry_price', 0)),
                    "sl_price": safe_float(getattr(t, 'sl_price', 0)),
                    "tp_price": safe_float(getattr(t, 'tp_price', 0)),
                    "volume": safe_float(getattr(t, 'volume', 0)),
                    "exit_price": safe_float(analysis_dict.get('exit_price', 0.0)),
                    "setup_id": getattr(t, 'setup_id', None),
                    "analysis_details": raw_analysis or "{}",
                    "pre_trade_checklist": checklist_data or "{}",
                    "images": getattr(t, 'images', "[]") or "[]",
                    "result_images": analysis_dict.get('result_images', '[]'),
                    "review_data": analysis_dict.get('review_data', '{}'),
                    "trade_class": analysis_dict.get('trade_class', ''),
                    "narrative": getattr(t, 'narrative', ""),
                    "created_at": int(getattr(t, 'created_at').timestamp()) if getattr(t, 'created_at', None) else 0,
                })
            return JsonResponse(results, safe=False)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def update_journal_review(request):
    """Cập nhật Nhật ký và tự động bù trừ tiền (Đã lắp radar)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            uuid = data.get('uuid')
            scenario = QuantScenario.objects.filter(uuid=uuid).first()
            
            if scenario:
                analysis_dict = {}
                # Dò lấy dữ liệu cũ
                raw_analysis = getattr(scenario, 'analysis_details', getattr(scenario, 'analysis', "{}"))
                try:
                    if raw_analysis: analysis_dict = json.loads(raw_analysis)
                except: pass
                
                # Nhét dữ liệu review mới vào
                analysis_dict['review_data'] = data.get('review_data', '{}')
                analysis_dict['result_images'] = data.get('result_images', '[]')
                analysis_dict['trade_class'] = data.get('trade_class', '')
                analysis_dict['exit_price'] = data.get('exit_price', 0.0)
                
                # Cập nhật ngược lại đúng cái cột mà Database đang dùng
                if hasattr(scenario, 'analysis_details'):
                    scenario.analysis_details = json.dumps(analysis_dict)
                else:
                    scenario.analysis = json.dumps(analysis_dict)
                
                # Tính toán lại PnL nếu sếp lén sửa tay
                old_pnl = float(getattr(scenario, 'pnl', 0.0) or 0.0)
                new_pnl = float(data.get('pnl', old_pnl))
                
                if old_pnl != new_pnl and scenario.status == 'CLOSED':
                    diff = new_pnl - old_pnl
                    scenario.pnl = new_pnl
                    acc = QuantAccount.objects.filter(id=scenario.account_id).first()
                    if acc:
                        acc.balance = float(acc.balance) + diff
                        acc.save()
                        
                scenario.save()
                return JsonResponse({"status": "ok"})
            return JsonResponse({"error": "Order sequence not found."}, status=404)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({"error": str(e)}, status=400)
        
# ==========================================
# PHẦN 6: TRẠM KIỂM ĐIỂM TUẦN (WEEKLY REVIEW)
# ==========================================
from .models import MissedTrade, WeeklyReview, WeeklyOutlook
import uuid

@csrf_exempt
def get_weekly_review_data(request):
    """Lấy dữ liệu Review và Outlook theo tuần"""
    if request.method == 'GET':
        account_id = request.GET.get('accountId', 1)
        week_start = request.GET.get('weekStart')
        
        review = WeeklyReview.objects.filter(account_id=account_id, week_start_date=week_start).first()
        outlook = WeeklyOutlook.objects.filter(account_id=account_id, week_start_date=week_start).first()
        
        return JsonResponse({
            "review": {
                "fa_accuracy": review.fa_accuracy,
                "ta_accuracy": review.ta_accuracy,
                "fusion_score": review.fusion_score,
                "review_details": review.review_details,
            } if review else None,
            "outlook": {
                "final_bias": outlook.final_bias,
                "script_plan": outlook.script_plan,
                "ta_bias": outlook.ta_bias,
                "fa_bias": outlook.fa_bias,
            } if outlook else None
        })

@csrf_exempt
def save_weekly_review_data(request):
    """Lưu Review và Outlook"""
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
                account_id=account_id, week_start_date=week_start,
                defaults={
                    "final_bias": outlook_data.get('final_bias', 'NEUTRAL'),
                    "script_plan": outlook_data.get('script_plan', ''),
                    "ta_bias": outlook_data.get('ta_bias', ''),
                    "fa_bias": outlook_data.get('fa_bias', '{}')
                }
            )
            return JsonResponse({"status": "ok"})
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
def handle_missed_trades(request):
    """Xử lý Lệnh lỡ (Missed Trades) nhập bằng tay"""
    if request.method == 'GET':
        account_id = request.GET.get('accountId', 1)
        week_start = request.GET.get('weekStart')
        missed = MissedTrade.objects.filter(account_id=account_id, week_start_date=week_start).order_by('-created_at')
        res = []
        for m in missed:
            res.append({
                "uuid": str(m.uuid), "pair": m.pair, "direction": m.direction,
                "reason": m.reason, "analysis_details": m.analysis_details,
                "images": m.images, "created_at": int(m.created_at.timestamp()) if m.created_at else 0
            })
        return JsonResponse(res, safe=False)
        
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            uuid_str = data.get('uuid')
            MissedTrade.objects.update_or_create(
                uuid=uuid_str if uuid_str else uuid.uuid4(),
                defaults={
                    "account_id": data.get('accountId', 1),
                    "week_start_date": data.get('weekStart'),
                    "pair": data.get('pair', ''),
                    "direction": data.get('direction', 'BUY'),
                    "reason": data.get('reason', ''),
                    "analysis_details": data.get('notes', ''),
                    "images": data.get('images', '[]')
                }
            )
            return JsonResponse({"status": "ok"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
            
    elif request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            MissedTrade.objects.filter(uuid=data.get('uuid')).delete()
            return JsonResponse({"status": "ok"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
        
# ==========================================
# PHẦN 7: RADAR & LIVE POSITIONS (MONITOR)
# ==========================================
@csrf_exempt
def get_active_trades(request):
    """Bơm danh sách lệnh đang sống lên Lò mổ Web"""
    if request.method == 'GET':
        try:
            account_id = request.GET.get('accountId', 1)
            active_scenarios = QuantScenario.objects.filter(account_id=account_id, status='ACTIVE').order_by('-created_at')
            res = []
            for s in active_scenarios:
                res.append({
                    "uuid": str(s.uuid),
                    "pair": s.pair,
                    "direction": s.direction,
                    "volume": float(s.volume),
                    "entry_price": float(s.entry_price),
                    "pnl": float(s.pnl) if s.pnl else 0.0,
                })
            return JsonResponse(res, safe=False)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def kill_switch_trade(request):
    """Kích hoạt Emergency Close từ Web"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            uuid_str = data.get('uuid')
            QuantScenario.objects.filter(uuid=uuid_str, status='ACTIVE').update(status='PENDING_CLOSE')
            return JsonResponse({"status": "ok", "message": "Emergency liquidation protocol transmitted to node."})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
def bridge_pending_closes(request):
    """Cổng cho EA MT5 quét lệnh cần chém khẩn cấp"""
    if request.method == 'GET':
        trade = QuantScenario.objects.filter(status='PENDING_CLOSE').first()
        if trade:
            return JsonResponse({"has_close_order": True, "uuid": str(trade.uuid), "pair": trade.pair})
        return JsonResponse({"has_close_order": False})
    
# ==========================================
# PHẦN 8: KHO VŨ KHÍ (SYSTEM LIBRARY)
# ==========================================
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

@csrf_exempt
def manage_system_library(request):
    import json
    import traceback
    
    try:
        # Ép import nằm trong lồng kính để tránh sập server nếu thiết kế DB lệch nhịp
        from .models import SystemLibrary
        
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
                # Cập nhật vũ khí
                SystemLibrary.objects.filter(id=item_id).update(
                    title=title,
                    category=category,
                    configuration=config_data
                )
            else:
                # Đúc vũ khí mới - Nhét sẵn chuỗi rỗng chống vỡ ống
                SystemLibrary.objects.create(
                    title=title,
                    category=category,
                    content="",      
                    image_path="",   
                    tags="",         
                    configuration=config_data
                )
            return JsonResponse({"status": "ok"})
            
        elif request.method == 'DELETE':
            data = json.loads(request.body)
            SystemLibrary.objects.filter(id=data.get('id')).delete()
            return JsonResponse({"status": "ok"})
            
        return JsonResponse({"error": "Method not allowed"}, status=405)

    except Exception as e:
        # Bắt gọn mọi loại lỗi và tát thẳng vào mặt React, cấm hiện HTML 500
        error_trace = traceback.format_exc()
        print("====== CRASH TẠI KHO VŨ KHÍ ======")
        print(error_trace)
        return JsonResponse({"error": f"CRITICAL SYSTEM FAILURE: {str(e)}"}, status=400)
    
# ==========================================
# PHẦN 9: TRUNG TÂM QUYỀN LỰC (CEO CONFIG)
# ==========================================
@csrf_exempt
def manage_system_config(request):
    """API GET/POST quản lý Vốn và Cầu dao tổng"""
    from .models import QuantAccount, PortfolioSetting, AccountWeight
    
    if request.method == 'GET':
        try:
            account_id = request.GET.get('accountId', 1)
            acc, _ = QuantAccount.objects.get_or_create(id=account_id, defaults={'name': 'Main Fund'})
            sett, _ = PortfolioSetting.objects.get_or_create(id=1)
            weight, _ = AccountWeight.objects.get_or_create(account=acc, defaults={'weight_percent': 100.0})

            return JsonResponse({
                "balance": acc.balance,
                "mode": sett.mode, 
                "max_risk": sett.max_daily_risk_percent,
                "account_weight": weight.weight_percent,
                "account_status": weight.status 
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            account_id = data.get('accountId', 1)

            acc = QuantAccount.objects.get(id=account_id)
            acc.balance = float(data.get('balance', acc.balance))
            acc.save()

            sett = PortfolioSetting.objects.get(id=1)
            sett.mode = data.get('mode', sett.mode)
            sett.save()

            weight = AccountWeight.objects.get(account=acc)
            weight.status = data.get('account_status', weight.status)
            weight.save()

            return JsonResponse({"status": "ok"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
def get_portfolio_state(request):
    """Cổng nội bộ cho Scenario Manager soi trạng thái quân luật"""
    from .models import QuantAccount, PortfolioSetting, AccountWeight
    try:
        account_id = request.GET.get('accountId', 1)
        acc = QuantAccount.objects.get(id=account_id)
        sett = PortfolioSetting.objects.get(id=1)
        weight = AccountWeight.objects.get(account=acc)

        return JsonResponse({
            "mode": sett.mode,
            "current_usd_bias": 0, 
            "account_status": weight.status,
            "account_weight": weight.weight_percent,
            "total_equity": acc.balance
        })
    except:
        return JsonResponse({"mode": "NORMAL", "account_status": "NORMAL", "account_weight": 100, "total_equity": 10000})

@csrf_exempt
def get_settings(request):
    from .models import QuantAccount
    try:
        acc = QuantAccount.objects.get(id=request.GET.get('accountId', 1))
        return JsonResponse({"initial_balance": acc.balance})
    except:
        return JsonResponse({"initial_balance": 10000})
    
# ==========================================
# PART 10: INSTITUTIONAL DASHBOARD METRICS
# ==========================================
@csrf_exempt
def get_dashboard_metrics(request):
    """Aggregate high-level metrics for the Landing Dashboard"""
    from .models import QuantAccount, QuantScenario, PortfolioSetting
    try:
        account_id = request.GET.get('accountId', 1)
        acc, _ = QuantAccount.objects.get_or_create(id=account_id, defaults={'name': 'Master Fund', 'balance': 10000})
        sett, _ = PortfolioSetting.objects.get_or_create(id=1)

        # Performance Metrics
        closed_trades = QuantScenario.objects.filter(account_id=account_id, status='CLOSED')
        total_closed = closed_trades.count()
        wins = closed_trades.filter(pnl__gt=0).count()
        win_rate = (wins / total_closed * 100) if total_closed > 0 else 0
        net_pnl = sum([t.pnl for t in closed_trades if t.pnl])

        # Live Exposure
        active_trades = QuantScenario.objects.filter(account_id=account_id, status='ACTIVE')
        active_exposure_lots = sum([t.volume for t in active_trades])
        floating_pnl = sum([t.pnl for t in active_trades if t.pnl])

        return JsonResponse({
            "aum": acc.balance,
            "net_pnl": net_pnl,
            "floating_pnl": floating_pnl,
            "win_rate": round(win_rate, 2),
            "total_trades": total_closed,
            "active_positions": active_trades.count(),
            "active_exposure": active_exposure_lots,
            "system_mode": sett.mode,
            "max_drawdown_limit": sett.max_daily_risk_percent
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)
    
# ==========================================
# PART 11: MACRO OUTLOOK & BIAS ENGINE
# ==========================================
@csrf_exempt
def manage_weekly_outlook(request):
    """API GET/POST cho trang Outlook (Macro Analysis)"""
    from .models import WeeklyOutlook
    
    if request.method == 'GET':
        try:
            week_start = request.GET.get('weekStart')
            account_id = request.GET.get('accountId', 1)
            
            outlook = WeeklyOutlook.objects.filter(account_id=account_id, week_start_date=week_start).first()
            if not outlook:
                return JsonResponse({"status": "empty"})
                
            return JsonResponse({
                "status": "ok",
                "fa_bias": outlook.fa_bias,
                "ta_bias": outlook.ta_bias,
                "final_bias": outlook.final_bias,
                "script_plan": outlook.script_plan
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            week_start = data.get('week_start_date')
            account_id = data.get('account_id', 1)
            
            outlook, created = WeeklyOutlook.objects.update_or_create(
                account_id=account_id,
                week_start_date=week_start,
                defaults={
                    'fa_bias': data.get('fa_bias', '{}'),
                    'ta_bias': data.get('ta_bias', ''),
                    'final_bias': data.get('final_bias', 'NEUTRAL'),
                    'script_plan': data.get('script_plan', '')
                }
            )
            return JsonResponse({"status": "ok", "message": "Macro Directive Synchronized."})
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({"error": str(e)}, status=400)