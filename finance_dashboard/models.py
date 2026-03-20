from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from django.utils import timezone
import uuid

# ==========================================
# PHẦN 1: WEBSITE CŨ (GIỮ NGUYÊN KHÔNG ĐỤNG CHẠM)
# ==========================================
class ForexPair(models.Model):
    pair = models.CharField(max_length=10, unique=True)
    current_rate = models.DecimalField(max_digits=12, decimal_places=5, null=True)
    last_updated = models.DateTimeField(auto_now=True)
    def __str__(self): return self.pair
    class Meta:
        ordering = ["pair"]
        verbose_name_plural = "Forex Pairs"
    @property
    def display_name(self):
        if len(self.pair) == 6: return f"{self.pair[:3]}/{self.pair[3:]}"
        return self.pair

class MacroData(models.Model):
    indicator = models.CharField(max_length=50)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    country = models.CharField(max_length=50)
    date = models.DateField()
    def __str__(self): return f"{self.indicator} - {self.country} - {self.date}"
    class Meta:
        ordering = ["date"]
        verbose_name_plural = "Macro Data"

class Insight(models.Model):
    CATEGORY_CHOICES = [("currency", "Currency"), ("stock", "Stock"), ("summary", "Summary"), ("other", "Other")]
    RESULT_CHOICES = [("positive", "Positive"), ("negative", "Negative"), ("neutral", "Neutral")]
    title = models.CharField(max_length=200)
    summary = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="other")
    date = models.DateTimeField(auto_now_add=True)
    result = models.CharField(max_length=10, choices=RESULT_CHOICES, default="neutral")
    reason = models.TextField(blank=True)
    analysis = models.TextField(blank=True)
    lessons = models.TextField(blank=True)
    metrics = models.JSONField(blank=True, null=True)
    portfolio_ref = models.ForeignKey("Portfolio", on_delete=models.SET_NULL, null=True, blank=True, related_name="insights")
    tags = models.TextField(blank=True, default="")
    content = models.TextField(blank=True, null=True)
    author = models.CharField(max_length=100, blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    attached_file = models.FileField(upload_to='insight_attachments/%Y/%m/%d/', blank=True, null=True)
    attached_image = models.ImageField(upload_to='insight_images/%Y/%m/%d/', blank=True, null=True)
    def __str__(self): return self.title
    class Meta:
        ordering = ["-date"]
        verbose_name_plural = "Insights"
    @property
    def has_attachment(self): return bool(self.attached_file or self.attached_image)
    @property
    def is_image(self):
        if self.attached_image: return True
        if self.attached_file: return self.attached_file.name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))
        return False
    @property
    def file_name(self):
        if self.attached_file: return self.attached_file.name.split('/')[-1]
        if self.attached_image: return self.attached_image.name.split('/')[-1]
        return None

class Portfolio(models.Model):
    CATEGORY_CHOICES = [("currency", "Currency"), ("stock", "Stock"), ("other", "Other")]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="currency")
    symbol = models.CharField(max_length=20, blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=10000)
    date_added = models.DateTimeField(auto_now_add=True)
    is_public = models.BooleanField(default=False)
    ref_insight = models.ForeignKey(Insight, on_delete=models.SET_NULL, null=True, blank=True, related_name="portfolio_references")
    def __str__(self): return f"{self.name} {self.symbol or ''}"
    @property
    def max_drawdown(self):
        trades = self.trades.order_by("date")
        if not trades.exists(): return 0
        equity = Decimal(self.amount)
        peak = equity
        max_dd = Decimal("0")
        for t in trades:
            equity += Decimal(str(t.pnl))
            peak = max(peak, equity)
            if peak > 0:
                dd = (peak - equity) / peak
                max_dd = max(max_dd, dd)
        return round(max_dd * 100, 2)
    class Meta:
        ordering = ["date_added"]
        verbose_name_plural = "Portfolios"

class Trade(models.Model):
    SIDE_CHOICES = [("BUY", "BUY"), ("SELL", "SELL")]
    TYPE_CHOICES = [("Live", "Live"), ("Backtest", "Backtest")]
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="trades")
    symbol = models.CharField(max_length=20, blank=True, null=True)
    side = models.CharField(max_length=10, choices=SIDE_CHOICES)
    entry = models.DecimalField(max_digits=12, decimal_places=5)
    exit = models.DecimalField(max_digits=12, decimal_places=5)
    stoploss = models.DecimalField(max_digits=12, decimal_places=5, null=True, blank=True)
    qty = models.IntegerField(default=10000)
    date = models.DateField()
    trade_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    notes = models.TextField(blank=True)
    ref = models.CharField(max_length=50, blank=True)
    ref_insight = models.ForeignKey(Insight, on_delete=models.SET_NULL, null=True, blank=True, related_name="trade_references")
    @property
    def pnl(self):
        direction = Decimal("1") if self.side == "BUY" else Decimal("-1")
        return round(direction * (self.exit - self.entry) * Decimal(self.qty), 2)
    @property
    def risk(self):
        if not self.stoploss: return None
        direction = Decimal("1") if self.side == "BUY" else Decimal("-1")
        return round(direction * (self.stoploss - self.entry) * Decimal(self.qty), 2)
    def __str__(self): return f"{self.portfolio.name} - {self.symbol} - {self.side}"
    class Meta:
        ordering = ["date"]
        verbose_name_plural = "Trades"

# ==========================================
# PHẦN 2: AUM TERMINAL & QUANT ENGINE
# ==========================================
class QuantAccount(models.Model):
    name = models.CharField(max_length=100)
    balance = models.FloatField(default=10000.0)
    currency = models.CharField(max_length=10, default='USD')
    mql5_path = models.CharField(max_length=500, blank=True, default="")
    lot_size = models.FloatField(default=100000.0)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name

class PortfolioSetting(models.Model):
    max_daily_risk_percent = models.FloatField(default=2.0)
    max_concurrent_risk_r = models.FloatField(default=5.0)
    mode = models.CharField(max_length=20, default='NORMAL')
    created_at = models.DateTimeField(auto_now_add=True)

class AccountWeight(models.Model):
    account = models.OneToOneField(QuantAccount, on_delete=models.CASCADE, primary_key=True)
    weight_percent = models.FloatField(default=0.0)
    status = models.CharField(max_length=20, default='NORMAL')
    last_updated = models.DateTimeField(auto_now=True)

class SystemLibrary(models.Model):
    category = models.CharField(max_length=50)
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    image_path = models.CharField(max_length=500, blank=True)
    tags = models.CharField(max_length=200, blank=True)
    configuration = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class QuantScenario(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(QuantAccount, on_delete=models.CASCADE)
    outlook_id = models.CharField(max_length=100, blank=True, null=True)
    pair = models.CharField(max_length=20)
    direction = models.CharField(max_length=10)
    setup_id = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, default='PENDING')
    entry_price = models.FloatField(default=0.0)
    sl_price = models.FloatField(default=0.0)
    tp_price = models.FloatField(default=0.0)
    volume = models.FloatField(default=0.01)
    pnl = models.FloatField(default=0.0)
    exit_price = models.FloatField(default=0.0)
    close_time = models.DateTimeField(null=True, blank=True)
    analysis_details = models.JSONField(default=dict, blank=True)
    pre_trade_checklist = models.JSONField(default=dict, blank=True)
    risk_data = models.JSONField(default=dict, blank=True)
    images = models.JSONField(default=list, blank=True)
    result_images = models.JSONField(default=list, blank=True)
    review_data = models.JSONField(default=dict, blank=True)
    execution_score = models.FloatField(default=0.0)
    htf_trend = models.CharField(max_length=50, blank=True)
    market_phase = models.CharField(max_length=50, blank=True)
    dealing_range = models.CharField(max_length=50, blank=True)
    narrative = models.TextField(blank=True)
    scenario_type = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class PortfolioRiskLog(models.Model):
    account = models.ForeignKey(QuantAccount, on_delete=models.CASCADE)
    pair = models.CharField(max_length=20)
    direction = models.CharField(max_length=10)
    requested_vol = models.FloatField()
    status = models.CharField(max_length=20)
    reason = models.CharField(max_length=200)
    timestamp = models.DateTimeField(auto_now_add=True)

# ==========================================
# KHU VỰC 3: TRẠM KIỂM ĐIỂM & NHẬN ĐỊNH
# ==========================================
class MissedTrade(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account_id = models.IntegerField(default=1)
    week_start_date = models.DateField()
    pair = models.CharField(max_length=20)
    direction = models.CharField(max_length=10)
    reason = models.CharField(max_length=100)
    analysis_details = models.TextField(blank=True, null=True)
    images = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.pair} - {self.reason}"

class WeeklyReview(models.Model):
    account_id = models.IntegerField(default=1)
    week_start_date = models.DateField()
    total_trades = models.IntegerField(default=0)
    win_rate = models.FloatField(default=0.0)
    net_pnl = models.FloatField(default=0.0)
    fa_accuracy = models.IntegerField(default=5)
    ta_accuracy = models.IntegerField(default=5)
    fusion_score = models.IntegerField(default=5)
    review_details = models.TextField(default="{}")
    class Meta:
        unique_together = ('account_id', 'week_start_date')
    def __str__(self): return f"Review Tuần: {self.week_start_date}"

class MacroDirective(models.Model):
    DIRECTION_CHOICES = [('BUY', 'LONG (BULLISH)'), ('SELL', 'SHORT (BEARISH)'), ('NEUTRAL', 'STAND CLEAR')]
    ticker = models.CharField(max_length=20, help_text="VD: XAUUSD, EURJPY")
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    week_start = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"MACRO: {self.ticker} -> {self.direction}"

class AlphaSignal(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'CHỜ DUYỆT (Radar)'),
        ('APPROVED', 'ĐÃ DUYỆT (Execute Node)'),
        ('REJECTED', 'BÁC BỎ (Thùng rác)'),
        ('EXECUTED', 'ĐANG CHẠY (Sàn MT5)'),
        ('CLOSED', 'CHỐT SỐ (Số cái PnL)')
    ]
    ticker = models.CharField(max_length=20)
    signal_direction = models.CharField(max_length=10)
    win_rate = models.FloatField(default=0.0)
    rr_ratio = models.FloatField(default=0.0)
    is_macro_aligned = models.BooleanField(default=True)
    kelly_recommended_lot = models.FloatField(default=0.0)
    ceo_approved_lot = models.FloatField(default=0.0, null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING')
    ticket_id = models.CharField(max_length=50, null=True, blank=True)
    realized_pnl = models.FloatField(default=0.0)
    pnl = models.FloatField(default=0.0, null=True, blank=True)  # <-- ĐÃ THỤT LỀ CHUẨN XÁC VÀO ĐÂY!
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self): return f"[{self.status}] {self.signal_direction} {self.ticker}"

class WeeklyOutlook(models.Model):
    week_start = models.DateField(unique=True)
    market_sentiment = models.CharField(max_length=50, default="MIXED")
    weekly_bias = models.CharField(max_length=50, default="NEUTRAL")
    execution_script = models.TextField(blank=True, null=True)
    fa_bias = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self): return f"OUTLOOK: {self.week_start} | Bias: {self.weekly_bias}"