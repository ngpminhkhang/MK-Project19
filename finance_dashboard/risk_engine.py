# MK/finance_dashboard/risk_engine.py

class KellyEngine:
    pass

class CentralRiskEngine:
    pass
class BehavioralRiskEngine:
    """
    Central Risk Engine: Rút củi dưới đáy nồi.
    Trị dứt điểm căn bệnh hưng phấn và trả thù thị trường.
    """
    def __init__(self, account_id):
        self.account_id = account_id
        self.base_risk_limit = 0.02 # Max 2% rủi ro cho mỗi lệnh chuẩn

    def calculate_oci(self, win_rate, avg_size, trade_freq):
        """
        Tính toán Overconfidence Index (OCI)
        """
        # Trọng số cảnh báo: Nếu Win Rate > 70% và nhồi lệnh liên tục -> OCI bùng nổ
        oci = (win_rate * 1.5) * avg_size * trade_freq
        return round(oci, 2)

    def adaptive_risk_dampening(self, current_streak, win_rate, avg_size, trade_freq):
        """
        Cơ chế tự động bóp nghẹt rủi ro (Self-Correcting)
        """
        oci_score = self.calculate_oci(win_rate, avg_size, trade_freq)
        current_risk_allowance = self.base_risk_limit

        system_action = "NORMAL"
        rationale = "Hệ thống ổn định. Cho phép duy trì rủi ro."

        # CẤP ĐỘ 1: RÚT CỦI NHẸ (Chuỗi thắng bắt đầu làm mờ lý trí)
        if current_streak >= 3 and oci_score > 0.6:
            current_risk_allowance = self.base_risk_limit * 0.8 # Giảm 20% đòn bẩy
            system_action = "RESTRICTED_L1"
            rationale = f"Phát hiện hưng phấn (OCI: {oci_score}). Cắt giảm 20% hạn mức vào lệnh."

        # CẤP ĐỘ 2: ĐẠP PHANH KHẨN CẤP (Ngáo quyền lực)
        elif current_streak >= 5 and oci_score > 0.8:
            current_risk_allowance = self.base_risk_limit * 0.5 # Bóp nghẹt 50%
            system_action = "RESTRICTED_L2"
            rationale = f"Chuỗi thắng {current_streak} lệnh. OCI vượt ngưỡng đỏ ({oci_score}). Ép giảm 50% kích thước vị thế."
            
        return {
            "allowed_risk": current_risk_allowance,
            "oci_score": oci_score,
            "action": system_action,
            "rationale": rationale
        }

# Chạy thử nghiệm hệ thống tại chỗ
if __name__ == "__main__":
    engine = BehavioralRiskEngine("MK_NODE_01")
    # Giả lập: Thắng 6 lệnh thông, win rate 85%, đánh khối lượng lớn
    result = engine.adaptive_risk_dampening(current_streak=6, win_rate=0.85, avg_size=1.2, trade_freq=4)
    print(f"Lệnh trừng phạt từ Core: {result}")