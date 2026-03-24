import logging
import numpy as np
from .models import AlphaSignal, QuantAccount

logger = logging.getLogger(__name__)

class BehavioralEngine:
    @staticmethod
    def analyze_trader_psyche():
        past_trades = AlphaSignal.objects.filter(status='CLOSED').order_by('-updated_at')[:20]
        if len(past_trades) < 5: return "STABLE", 1.0, 0.0 
        
        wins = [t for t in past_trades if t.pnl and float(t.pnl) > 0]
        win_rate = len(wins) / len(past_trades)
        
        win_streak = 0
        for t in past_trades:
            if t.pnl and float(t.pnl) > 0: win_streak += 1
            else: break
            
        pnls = [float(t.pnl) for t in past_trades if t.pnl]
        volatility = np.std(pnls) if pnls else 0
        oci = win_rate * win_streak * (volatility / 100 + 1)
        
        if win_streak >= 4 or oci > 5.0: return "HOT", 0.8, oci 
        return "STABLE", 1.0, oci

class KellyEngine:
    @staticmethod
    def calculate_final_bullet(capital, win_rate=0.5, rr_ratio=2.0):
        regime, penalty, oci = BehavioralEngine.analyze_trader_psyche()
        if regime == "TILT": return 0.0
        
        raw_kelly = win_rate - ((1.0 - win_rate) / rr_ratio)
        final_allocation = (capital * (raw_kelly / 2.0)) * penalty 
        return round(max(0.0, final_allocation), 2)

class CentralRiskEngine:
    HARD_LIMIT_PCT = 30.0

    @staticmethod
    def get_total_notional_exposure():
        active = AlphaSignal.objects.filter(status__in=['EXECUTED', 'APPROVED'])
        return sum([(s.ceo_approved_lot or 0) * 100000 * (s.entry_price or 1.0) for s in active])

    @classmethod
    def validate_new_trade(cls, balance, new_lot, price):
        current_exp = cls.get_total_notional_exposure()
        new_exp = (new_lot * 100000 * price)
        total_pct = ((current_exp + new_exp) / balance) * 100 if balance > 0 else 100
        
        if total_pct > cls.HARD_LIMIT_PCT:
            return False, f"TỪ CHỐI! Exposure {total_pct:.2f}% vượt ngưỡng 30%."
        return True, f"An toàn. Exposure hiện tại: {total_pct:.2f}%."