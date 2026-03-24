from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import AlphaSignal
from .risk_services import process_signal_vetting
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=AlphaSignal)
def trigger_risk_vetting(sender, instance, created, **kwargs):
    """
    Giao liên bắt tín hiệu khi AlphaSignal lưu vào cơ sở dữ liệu.
    Chỉ kích hoạt kiểm duyệt rủi ro với lệnh mới hoặc lệnh PENDING.
    """
    if created or instance.status == 'PENDING':
        logger.info(f"Signal giao liên kích hoạt cho lệnh: {instance.ticker}")
        process_signal_vetting(instance.id)