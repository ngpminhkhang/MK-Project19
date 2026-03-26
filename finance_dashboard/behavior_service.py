def calculate_oci(account_id):
    """
    ALGO RÚT CỦI ĐÁY NỒI: Tính toán mức độ 'ngáo quyền lực'.
    """
    metrics = BehaviorMetrics.objects.get(account_id=account_id)
    
    # OCI = (WinRate * AvgRisk * TradeFrequency) [cite: 150, 413-417]
    # Nếu Win streak > 5 và Lot size lệnh sau > lệnh trước 20% -> HOT
    if metrics.win_streak >= 5:
        metrics.oci_score = min(1.0, metrics.oci_score + 0.15)
        metrics.state = "HOT"
    
    if metrics.oci_score > 0.8:
        metrics.state = "TILT" # Trạng thái 'say máu', cần khóa mõm [cite: 726, 732]
        
    metrics.save()
    return metrics