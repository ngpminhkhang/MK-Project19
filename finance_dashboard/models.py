from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from django.utils import timezone
import uuid

# --- CƠ SỞ DỮ LIỆU DI SẢN (LEGACY) ---
class ForexPair(models.Model):
    pair = models.CharField(max_length=10, unique=True)
    current_rate = models.DecimalField(max_digits=12, decimal_places=5, null=True)
    last_updated = models.DateTimeField(auto_now=True)
    def __str__(self): return self.pair
    class Meta:
        ordering = ["pair"]
        verbose_name_plural = "Forex Pairs"

class MacroData(models.Model):
    indicator = models.CharField(max_length=50)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    country = models.CharField(max_length=50)
    date = models.DateField()
    def __str__(self): return f"{self.indicator} - {self.country}"
    class Meta:
        ordering = ["date"]
        verbose_name_plural = "Macro Data"

class Portfolio(models.Model):
    name = models.CharField(max_length=100, default='My Portfolio')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    buy_date = models.DateField(auto_now_add=True)
    is_public = models.BooleanField(default=False)
    def __str__(self): return f"{self.name} - {self.amount}"

class Trade(models.Model):
    STATUS_CHOICES = [('OPEN', 'Open'), ('CLOSED', 'Closed'), ('PENDING', 'Pending')]
    SIDE_CHOICES = [('BUY', 'Buy'), ('SELL', 'Sell')]
    forex_pair = models.ForeignKey(ForexPair, on_delete=models.CASCADE, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    side = models.CharField(max_length=4, choices=SIDE_CHOICES, default='BUY')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='OPEN')
    open_rate = models.DecimalField(max_digits=12, decimal_places=5, null=True, blank=True)
    close_rate = models.DecimalField(max_digits=12, decimal_places=5, null=True, blank=True)
    stoploss = models.DecimalField(max_digits=12, decimal_places=5, null=True, blank=True)
    takeprofit = models.DecimalField(max_digits=12, decimal_places=5, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    pnl = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    open_date = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.side} {self.amount}"

class Insight(models.Model):
    title = models.CharField(max_length=200)
    date = models.DateTimeField(default=timezone.now)
    content = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    market_context = models.TextField(blank=True, null=True)
    key_levels = models.TextField(blank=True, null=True)
    trade_plan = models.TextField(blank=True, null=True)
    result = models.CharField(max_length=100, blank=True, null=True)
    lessons_learned = models.TextField(blank=True, null=True)
    tags = models.CharField(max_length=200, blank=True, null=True)
    attached_image = models.ImageField(upload_to='insights/images/', blank=True, null=True)
    attached_file = models.FileField(upload_to='insights/files/', blank=True, null=True)
    def __str__(self): return self.title

# --- HỆ THỐNG QUẢN TRỊ (AUM & RISK) ---
class QuantAccount(models.Model):
    account_name = models.CharField(max_length=100)
    balance = models.FloatField(default=0.0)
    equity = models.FloatField(default=0.0)
    margin = models.FloatField(default=0.0)
    free_margin = models.FloatField(default=0.0)
    margin_level = models.FloatField(default=0.0)
    account_currency = models.CharField(max_length=10, default="USD")
    status = models.CharField(max_length=20, default="NORMAL") 
    last_updated = models.DateTimeField(auto_now=True)
    def __str__(self): return f"{self.account_name} - Equity: {self.equity}"

class AlphaSignal(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending AI/CEO Check'), 
        ('APPROVED', 'Approved'), 
        ('REJECTED', 'Rejected'), 
        ('EXECUTED', 'Sent to Broker'), 
        ('CLOSED', 'Closed')
    ]
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    ticker = models.CharField(max_length=20)
    signal_direction = models.CharField(max_length=10)
    entry_price = models.FloatField(null=True, blank=True)
    ceo_approved_lot = models.FloatField(null=True, blank=True)
    sl = models.FloatField(null=True, blank=True)
    tp = models.FloatField(null=True, blank=True)
    pnl = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    analysis_details = models.TextField(default="{}")
    pre_trade_checklist = models.TextField(default="{}")
    review_data = models.TextField(default="{}")
    images = models.TextField(default="[]")
    result_images = models.TextField(default="[]")
    htf_trend = models.CharField(max_length=20, blank=True, null=True)
    market_phase = models.CharField(max_length=50, blank=True, null=True)
    dealing_range = models.CharField(max_length=100, blank=True, null=True)
    narrative = models.TextField(blank=True, null=True)
    scenario_type = models.CharField(max_length=50, blank=True, null=True)
    trade_class = models.CharField(max_length=10, blank=True, null=True)
    exit_price = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self): return f"[{self.status}] {self.ticker}"

class RiskLog(models.Model):
    signal = models.ForeignKey(AlphaSignal, on_delete=models.CASCADE, null=True, related_name='risk_logs')
    decision = models.CharField(max_length=20)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"[{self.decision}] {self.signal.ticker if self.signal else 'Unknown'}"

# --- CÁC MODEL PHỤ TRỢ ---
class MacroDirective(models.Model):
    title = models.CharField(max_length=100)
    def __str__(self): return self.title

class SystemLibrary(models.Model):
    category = models.CharField(max_length=20)
    title = models.CharField(max_length=100)
    configuration = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True, null=True) # Đã bọc thép null=True
    def __str__(self): return self.title

class MissedTrade(models.Model):
    pair = models.CharField(max_length=20, null=True)
    direction = models.CharField(max_length=10, default='BUY')
    reason = models.CharField(max_length=50, null=True)
    notes = models.TextField(null=True)
    image_paths = models.TextField(default="[]")
    created_at = models.DateTimeField(auto_now_add=True, null=True) # FIX: Thêm null=True tại đây
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

class WeeklyOutlook(models.Model):
    week_start = models.DateField(unique=True)
    weekly_bias = models.CharField(max_length=20, default='NEUTRAL')
    execution_script = models.TextField(blank=True)
    fa_bias = models.TextField(default="{}")
    def __str__(self): return str(self.week_start)

class RadarBlip(models.Model):
    symbol = models.CharField(max_length=20, unique=True)
    def __str__(self): return self.symbol

class PortfolioSetting(models.Model):
    account = models.OneToOneField(QuantAccount, on_delete=models.CASCADE, related_name='settings')
    target_profit_monthly = models.FloatField(default=5.0)
    max_drawdown_limit = models.FloatField(default=10.0)
    max_risk_per_trade = models.FloatField(default=1.0)
    def __str__(self): return f"Settings for {self.account.account_name}"