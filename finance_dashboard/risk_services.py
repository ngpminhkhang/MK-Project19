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

def process_oci_impact(account_id, new_lot_size):
    """
    Hàm 'Xích quái vật': Tính toán và cập nhật chỉ số hưng phấn (OCI).
    """
    try:
        # 1. Lấy hoặc tạo mới metrics cho tài khoản
        metrics, created = PerformanceMetrics.objects.get_or_create(account_id=account_id)
        
        # 2. Logic 'Rút củi đáy nồi': 
        # Nếu sếp đánh Lot size > 2.0, hệ thống coi là bắt đầu 'say máu'
        lot_val = float(new_lot_size)
        if lot_val > 2.0:
            # Tăng điểm OCI mỗi khi sếp bung lụa
            metrics.oci_index = min(1.0, metrics.oci_index + 0.05)
            
            # 3. Kích hoạt 'Hố đào hội đồng': Ghi log khi OCI đạt mức HOT (> 0.8)
            if metrics.oci_index > 0.8:
                BehaviorAudit.objects.create(
                    account_id=account_id,
                    event_label="OCI_SPIKE",
                    severity="CRITICAL",
                    description=f"Hệ thống phát hiện trạng thái Euphoria (Hưng phấn quá đà). Lot size {lot_val} vượt ngưỡng an toàn hành vi.",
                    timestamp=timezone.now()
                )
        
        metrics.save()
        return metrics.oci_index
    except Exception as e:
        print(f"Lỗi OCI Engine: {e}")
        return 0