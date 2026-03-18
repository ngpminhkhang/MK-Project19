from django.contrib import admin
from .models import (
    ForexPair, MacroData, Portfolio, # Các bảng cũ sếp đang có
    QuantAccount, PortfolioSetting, AccountWeight, SystemLibrary, QuantScenario, PortfolioRiskLog, MissedTrade, WeeklyReview, WeeklyOutlook # Đội quân mới
)

# === WEBSITE CŨ ===
admin.site.register(ForexPair)
admin.site.register(MacroData)
admin.site.register(Portfolio)

# === AUM TERMINAL & QUANT ENGINE ===
@admin.register(QuantAccount)
class QuantAccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'balance', 'currency')

@admin.register(AccountWeight)
class AccountWeightAdmin(admin.ModelAdmin):
    list_display = ('account', 'weight_percent', 'status')

@admin.register(SystemLibrary)
class SystemLibraryAdmin(admin.ModelAdmin):
    list_display = ('title', 'category')

admin.site.register(PortfolioSetting)
admin.site.register(QuantScenario)
admin.site.register(PortfolioRiskLog)

admin.site.register(MissedTrade)
admin.site.register(WeeklyReview)
admin.site.register(WeeklyOutlook)