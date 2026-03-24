from django import forms
from .models import Portfolio, Trade, Insight, MacroData, ForexPair

# ===================== KHAI BÁO CƠ BẢN ================================

FOREX_CHOICES = [
    ("EURUSD=X", "EUR/USD"),
    ("GBPUSD=X", "GBP/USD"),
    ("USDJPY=X", "USD/JPY"),
    ("AUDUSD=X", "AUD/USD"),
    ("USDCAD=X", "USD/CAD"),
    ("USDCHF=X", "USD/CHF"),
    ("NZDUSD=X", "NZD/USD"),
]

INTERVAL_CHOICES = [
    ("1d", "1 Day"),
    ("1h", "1 Hour"),
    ("30m", "30 Minutes"),
    ("15m", "15 Minutes"),
    ("1wk", "1 Week"),
    ("1mo", "1 Month"),
]

# Áo giáp chống lỗi cho InsightSearchForm
INSIGHT_CATEGORIES = [
    ("Macro", "Macro"),
    ("Technical", "Technical"),
    ("Psychology", "Psychology"),
    ("Risk", "Risk Management"),
]

class WatchlistFilterForm(forms.Form):
    pairs = forms.MultipleChoiceField(
        choices=FOREX_CHOICES,
        initial=["EURUSD=X", "GBPUSD=X", "USDJPY=X"],
        widget=forms.CheckboxSelectMultiple,
        label="Chọn cặp Forex"
    )
    
    interval = forms.ChoiceField(
        choices=INTERVAL_CHOICES,
        initial="1d",
        label="Khung thời gian"
    )
    rsi = forms.BooleanField(required=False, initial=False, label="Hiển thị RSI")
    macd = forms.BooleanField(required=False, initial=False, label="Hiển thị MACD")
    bb = forms.BooleanField(required=False, initial=False, label="Hiển thị Bollinger Bands")

# ===================== CÁC FORM NHẬP LIỆU ================================

class TechnicalForm(forms.Form):
    symbol = forms.CharField(max_length=20, label="Mã Giao Dịch", initial="XAUUSD=X")
    interval = forms.ChoiceField(choices=INTERVAL_CHOICES, initial="1h", label="Khung Thời Gian")

class MacroForm(forms.ModelForm):
    class Meta:
        model = MacroData
        fields = ['indicator', 'value', 'country', 'date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

class TradeForm(forms.ModelForm):
    class Meta:
        model = Trade
        fields = ['forex_pair', 'amount', 'side', 'open_rate', 'close_rate', 'stoploss', 'takeprofit', 'status', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class PortfolioForm(forms.ModelForm):
    class Meta:
        model = Portfolio
        fields = ['name', 'amount', 'is_public']

class InsightForm(forms.ModelForm):
    class Meta:
        model = Insight
        fields = ['title', 'category', 'date', 'market_context', 'key_levels', 'trade_plan', 'result', 'lessons_learned', 'tags', 'attached_image', 'attached_file']
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'market_context': forms.Textarea(attrs={'rows': 3}),
            'key_levels': forms.Textarea(attrs={'rows': 3}),
            'trade_plan': forms.Textarea(attrs={'rows': 3}),
            'lessons_learned': forms.Textarea(attrs={'rows': 3}),
        }

class InsightSearchForm(forms.Form):
    q = forms.CharField(required=False, label="Tìm kiếm")
    # Gắn băng đạn INSIGHT_CATEGORIES vào đây để tránh lỗi thuộc tính
    category = forms.ChoiceField(choices=[("", "Tất cả")] + INSIGHT_CATEGORIES, required=False, label="Danh mục")
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

class TradeInsightForm(forms.Form):
    """Form để gán hoặc tạo Insight cho Trade"""
    insight = forms.ModelChoiceField(
        queryset=Insight.objects.all(),
        required=False,
        label="Chọn Insight có sẵn"
    )
    
    new_title = forms.CharField(
        max_length=200,
        required=False,
        label="Hoặc tạo Insight mới (nhập tiêu đề)"
    )

    def clean(self):
        cleaned_data = super().clean()
        insight = cleaned_data.get("insight")
        new_title = cleaned_data.get("new_title")
        
        if not insight and not new_title:
            raise forms.ValidationError("Bạn phải chọn Insight hoặc nhập tiêu đề mới.")
        return cleaned_data

class TradeFilterForm(forms.Form):
    """Form để lọc trades theo loại"""
    trade_type = forms.ChoiceField(
        choices=[("", 'All')] + Trade.SIDE_CHOICES,
        required=False,
        label="Filter Side"  
    )

class GlobalSearchForm(forms.Form):
    q = forms.CharField(
        label="",
        widget=forms.TextInput(attrs={
            'placeholder': 'Search symbol...',
            'class': 'search-input'
        })
    )