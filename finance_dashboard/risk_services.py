from django.db import transaction
from .models import AlphaSignal, RiskLog, QuantAccount
import logging

logger = logging.getLogger(__name__)

@transaction.atomic
def process_signal_vetting(signal_id):
    """
    HÀM KIỂM DUYỆT RỦI RO CHI TIẾT
    """
    try:
        signal = AlphaSignal.objects.select_for_update().get(id=signal_id)
        account = QuantAccount.objects.first()
        
        if not account:
            logger.warning("Vetting failed: No QuantAccount found.")
            return False

        lot_size = float(signal.ceo_approved_lot or 0)
        exposure = lot_size * 100000 
        
        capital = account.equity if account.equity > 0 else account.balance
        max_allowed = float(capital) * 0.30 
        
        if exposure > max_allowed:
            # Dùng filter().update() để tránh gọi lại hàm save() gây vòng lặp
            AlphaSignal.objects.filter(id=signal_id).update(status='REJECTED')
            
            RiskLog.objects.create(
                signal=signal,
                decision='REJECTED',
                reason=f"TỪ CHỐI: Exposure ${exposure:,.2f} vượt ngưỡng 30% vốn (${max_allowed:,.2f})"
            )
            return False
            
        RiskLog.objects.create(
            signal=signal,
            decision='APPROVED',
            reason=f"CHẤP THUẬN: Exposure ${exposure:,.2f} nằm trong giới hạn cho phép."
        )
        return True
    except Exception as e:
        logger.error(f"Critical Risk Engine Error: {str(e)}")
        return False

class ExecutionService:
    """
    Dịch vụ Thực thi lệnh - Giữ lại để không lỗi views.py
    """
    @staticmethod
    def execute_signal(signal_id):
        # Logic thực thi lệnh sẽ được triển khai sau
        pass