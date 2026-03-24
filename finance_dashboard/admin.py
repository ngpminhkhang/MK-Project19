from django.contrib import admin
from .models import (
    ForexPair, MacroData, Portfolio, Trade, Insight, 
    QuantAccount, PortfolioSetting, SystemLibrary, 
    MissedTrade, WeeklyReview, WeeklyOutlook, MacroDirective,
    AlphaSignal, RadarBlip, RiskLog 
)

# --- WEBSITE CŨ (TẦNG 1) ---
admin.site.register(ForexPair)
admin.site.register(MacroData)
admin.site.register(Portfolio)
admin.site.register(Trade)
admin.site.register(Insight)
admin.site.register(MacroDirective)

# --- AUM TERMINAL & QUANT ENGINE (TẦNG 2) ---
@admin.register(QuantAccount)
class QuantAccountAdmin(admin.ModelAdmin):
    list_display = ('account_name', 'balance', 'status', 'last_updated')
    list_filter = ('status',)

@admin.register(AlphaSignal)
class AlphaSignalAdmin(admin.ModelAdmin):
    list_display = ('ticker', 'signal_direction', 'status', 'ceo_approved_lot', 'created_at')
    list_filter = ('status', 'ticker')
    search_fields = ('ticker', 'uuid')

@admin.register(RiskLog)
class RiskLogAdmin(admin.ModelAdmin):
    list_display = ('get_ticker', 'decision', 'reason', 'created_at')
    list_filter = ('decision',)
    
    def get_ticker(self, obj):
        return obj.signal.ticker if obj.signal else "Global/System"
    get_ticker.short_description = 'Asset'

admin.site.register(SystemLibrary)
admin.site.register(PortfolioSetting)
admin.site.register(MissedTrade)
admin.site.register(WeeklyReview)
admin.site.register(WeeklyOutlook)
admin.site.register(RadarBlip)