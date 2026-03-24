from django.urls import path
from . import views, api

urlpatterns = [
    # --- WEBSITE FRONTEND ---
    path('', views.home, name='home'),
    path('analysis/', views.analysis, name='analysis'),
    path('portfolio/', views.portfolio, name='portfolio'),
    path('about/', views.about, name='about'),
    path('search/', views.search_view, name='search'),
    path('insights/', views.insights, name='insights'),

    # --- HỆ THỐNG API (FIX LỖI 404 TẠI ĐÂY) ---
    # Radar & Logs
    path('api/exposure_radar/', api.exposure_radar_api, name='api_exposure_radar'),
    path('api/risk_logs/', api.get_risk_logs, name='api_get_risk_logs'),
    
    # Journal & Trades
    path('api/journal/trades/', api.get_journal_trades, name='api_journal_trades'),
    
    # Metrics & Rebalance
    path('api/portfolio/metrics/', api.get_portfolio_metrics, name='api_portfolio_metrics'),
    path('api/portfolio/rebalance/', api.apply_portfolio_rebalance, name='api_rebalance'),
    
    # Review & Outlook
    path('api/review/save/', api.save_weekly_review_data, name='api_review_save'),
    path('api/outlook/current/', api.get_current_outlook, name='api_get_outlook'),
]