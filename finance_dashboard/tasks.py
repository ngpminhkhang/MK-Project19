import json
import logging
from celery import shared_task
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import AlphaSignal, QuantAccount, RiskLog
from .risk_engine import CentralRiskEngine, BehavioralEngine, KellyEngine

logger = logging.getLogger(__name__)

@shared_task
def monitor_portfolio_risk_task():
    """
    NHIỆM VỤ TUẦN TRA (QUÉT MỖI GIÂY)
    Tính toán Exposure, Drawdown và đẩy lên bảng điện tử WebSocket.
    """
    channel_layer = get_channel_layer()
    account = QuantAccount.objects.first()
    
    if not account:
        return "No account found"

    # 1. Tính toán Notional Exposure thực tế
    total_exposure = CentralRiskEngine.get_total_notional_exposure()
    exposure_pct = (total_exposure / account.balance * 100) if account.balance > 0 else 0
    
    # 2. Quét nhịp đập tâm lý
    win_streak, lose_streak = BehavioralEngine.get_trade_streaks()
    oci = BehavioralEngine.calculate_oci(win_streak)

    # 3. Đóng gói dữ liệu tình báo
    metrics_data = {
        "balance": float(account.balance),
        "equity": float(account.equity),
        "total_exposure": round(total_exposure, 2),
        "exposure_pct": round(exposure_pct, 2),
        "win_streak": win_streak,
        "oci": round(oci, 2),
        "timestamp": timezone.now().strftime("%H:%M:%S")
    }

    # 4. BẮN DỮ LIỆU LÊN BẢNG ĐIỆN TỬ (Daphne/WebSocket)
    async_to_sync(channel_layer.group_send)(
        f'terminal_{account.id}',
        {
            'type': 'send_metrics',
            'data': metrics_data
        }
    )
    
    # 5. TỰ ĐỘNG NGẮT ĐIỆN (SAFETY BREAKER)
    if exposure_pct > 30.0:
        logger.critical(f"HARD LIMIT BREACHED: {exposure_pct}%! Cảnh báo CEO khẩn cấp.")
        # Sếp có thể thêm logic tự động đóng lệnh (Force Reduce) ở đây nếu muốn

    return f"Patrol finished: OCI {oci} | Exp {exposure_pct}%"

@shared_task
def broadcast_new_signal_task(signal_id):
    """
    NHIỆM VỤ THÔNG BÁO LỆNH MỚI
    Khi có tín hiệu từ MT5/TradingView, đẩy ngay lên màn hình duyệt của sếp.
    """
    try:
        signal = AlphaSignal.objects.get(id=signal_id)
        channel_layer = get_channel_layer()
        
        async_to_sync(channel_layer.group_send)(
            'radar_group',
            {
                'type': 'new_signal',
                'data': {
                    "id": signal.id,
                    "ticker": signal.ticker,
                    "direction": signal.signal_direction,
                    "status": signal.status,
                    "time": signal.created_at.strftime("%H:%M:%S")
                }
            }
        )
    except Exception as e:
        logger.error(f"Failed to broadcast signal: {e}")