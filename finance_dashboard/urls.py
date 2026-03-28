from django.urls import path
from . import views, api

urlpatterns = [
    # --- WEBSITE FRONTEND ---
    path('', api.system_health_check, name='home'),
    path('analysis/', views.analysis, name='analysis'),
    path('portfolio/', views.portfolio, name='portfolio'),
    path('about/', views.about, name='about'),
    path('search/', views.search_view, name='search'),

    # --- HỆ THỐNG API (DÀNH CHO AUDIT HUB) ---
    path('api/exposure_radar/', api.exposure_radar_api, name='api_exposure_radar'),
    path('api/risk_logs/', api.get_risk_logs, name='api_get_risk_logs'),
    path('api/journal/trades/', api.get_journal_trades, name='api_journal_trades'),
    
    # Quản lý & Review
    path('api/portfolio/metrics/', api.get_portfolio_metrics, name='api_get_portfolio_metrics'),
    path('api/review/save/', api.save_weekly_review_data, name='api_review_save'),
    path('api/outlook/current/', api.get_current_outlook, name='api_get_outlook'),
    
    # Signal & Execution (Cầu nối MT5)
    path('api/scenarios/', api.get_scenarios, name='api_get_scenarios'),
    path('api/mt5/execution/', api.mt5_execution_node, name='api_mt5_execution'),

    path('api/stress_test/', api.get_stress_test, name='api_stress_test'),
    path('api/mt5/direct_fire/', views.mt5_direct_fire_api, name='mt5_direct_fire'),

    path('api/v1/dashboard/', api.get_quant_dashboard_data, name='api_quant_dashboard'),

    path('api/v1/alpha-engine/', api.get_alpha_engine_data, name='api_alpha_engine'),
    path('api/v1/risk-engine/', api.get_risk_engine_data, name='api_risk_engine'),
    path('api/v1/behavioral-analytics/', api.get_behavioral_analytics_data, name='api_behavioral_analytics'),
]