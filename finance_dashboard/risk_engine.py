import logging

logger = logging.getLogger(__name__)

class KellyEngine:
    """
    Cỗ máy phân bổ vốn toán học. Không cảm xúc.
    """

    @staticmethod
    def _raw_kelly(win_rate: float, reward_risk_ratio: float) -> float:
        """ Tính toán Kelly nguyên thủy """
        if reward_risk_ratio <= 0:
            return 0.0
        
        kelly_pct = win_rate - ((1.0 - win_rate) / reward_risk_ratio)
        return max(0.0, kelly_pct) # Âm thì trả về 0 (Đứng im)

    @staticmethod
    def get_full_kelly(win_rate: float, reward_risk_ratio: float) -> float:
        """ 
        Dành cho kẻ điên. Cược tối đa theo giới hạn toán học.
        Khả năng x2 tài khoản cao, nhưng sụt giảm (Drawdown) cực sốc.
        """
        return KellyEngine._raw_kelly(win_rate, reward_risk_ratio)

    @staticmethod
    def get_half_kelly(win_rate: float, reward_risk_ratio: float) -> float:
        """ 
        Tiêu chuẩn Quỹ Phòng Hộ. Ăn chia sự an toàn. 
        Giảm một nửa tốc độ tăng trưởng nhưng đập nát rủi ro phá sản.
        """
        return KellyEngine._raw_kelly(win_rate, reward_risk_ratio) / 2.0


class FundManager:
    """
    Giám đốc rủi ro. Chuyên gia dội nước lạnh vào mặt CEO.
    """

    @staticmethod
    def anti_euphoria_protocol(initial_capital: float, current_balance: float, current_throttle: float = 1.0) -> float:
        """
        Thuật toán Giảm Hưng Phấn.
        initial_capital: Vốn gốc (Ví dụ: 100,000)
        current_balance: Vốn hiện tại (Ví dụ: 200,000)
        current_throttle: Tỷ lệ vốn đang được phép dùng (Bắt đầu là 1.0 -> 100%)
        
        Trả về: Hệ số cấp vốn mới cho tháng tiếp theo.
        """
        roi = (current_balance - initial_capital) / initial_capital

        # Sếp vừa nhân đôi tài khoản? (ROI >= 100%)
        if roi >= 1.0:
            logger.warning("CEO MODE ĐANG NGÁO ĐÁ. Kích hoạt giao thức tước vũ khí!")
            
            # Cắt giảm 20% quyền lực
            new_throttle = current_throttle - 0.20
            
            # Chạm đáy nỗi đau (Chỉ còn 50% vốn) thì bắt đầu bơm lại từ từ
            if new_throttle <= 0.50:
                logger.info("Chạm ngưỡng an toàn. Bắt đầu nới lỏng dòng vốn.")
                # Công thức bơm lại 10% mỗi lần sếp vượt đỉnh mới (Sếp tự điều chỉnh con số này)
                new_throttle = min(1.0, current_throttle + 0.10) 
                
            return round(new_throttle, 2)
        
        # Sếp đang trade bình thường, chưa x2 tài khoản
        return current_throttle

    @staticmethod
    def calculate_final_bullet(capital: float, win_rate: float, rr_ratio: float, throttle_rate: float, use_half_kelly: bool = True) -> float:
        """
        Hàm chốt hạ. Tổng hợp mọi hình phạt và tính ra số tiền tươi thóc thật được phép ném vào lệnh này.
        """
        # Bước 1: Tính phần trăm theo Kelly
        if use_half_kelly:
            kelly_pct = KellyEngine.get_half_kelly(win_rate, rr_ratio)
        else:
            kelly_pct = KellyEngine.get_full_kelly(win_rate, rr_ratio)

        # Bước 2: Bóp nghẹt vốn tổng theo độ ngáo đá của sếp
        usable_capital = capital * throttle_rate

        # Bước 3: Tính ra số đạn cuối cùng
        bullet = usable_capital * kelly_pct
        
        logger.info(f"Vốn khả dụng: {usable_capital}. Tỷ lệ Kelly: {kelly_pct}. Đạn nạp: {bullet}")
        return round(bullet, 2)