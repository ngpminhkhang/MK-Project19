from django.urls import path
from . import views, api

urlpatterns = [
    # --- TẦNG 1: WEBSITE TRUYỀN THỐNG (CÁC THẺ {% url %} ĐANG GỌI VÀO ĐÂY) ---
    path('', views.home, name='home'),
    path('analysis/', views.analysis, name='analysis'),
    path('analysis/ajax/', views.analysis_ajax, name='analysis_ajax'),
    path('portfolio/', views.portfolio, name='portfolio'),
    path('about/', views.about, name='about'),
    path('insights/', views.insights, name='insights'),
    path('details/<str:symbol>/', views.details, name='details'),
    
    # CỔNG SEARCH (FIX LỖI TẠI DÒNG 198 TRONG FILE HTML CỦA SẾP)
    path('search/', views.search_view, name='search'),
    path('chart/<str:symbol>/', views.chart_view, name='chart'),

    # --- TẦNG 2: AUM TERMINAL & RISK ENGINE (DÀNH CHO REACT/TAURI) ---
    
    # Radar & Logs (Hệ thống Audit mới)
    path('api/exposure_radar/', api.exposure_radar_api, name='api_exposure_radar'),
    path('api/risk_logs/', api.get_risk_logs, name='api_get_risk_logs'),
    
    # Quản lý danh mục & Metrics
    path('api/portfolio/metrics/', api.get_portfolio_metrics, name='api_portfolio_metrics'),
    path('api/portfolio/rebalance/', api.apply_portfolio_rebalance, name='api_rebalance'),
    
    # Signal & Execution (Cầu nối MT5)
    path('api/scenarios/', api.get_scenarios, name='api_scenarios'),
    path('api/mt5/execution/', api.mt5_execution_node, name='api_mt5_execution'),
    path('api/mt5/confirm/', api.bridge_confirm_execution, name='api_mt5_confirm'),
    path('api/mt5/sync_pnl/', api.bridge_sync_live_pnl, name='api_sync_pnl'),
    
    # Nhật ký & Review
    path('api/journal/trades/', api.get_journal_trades, name='api_journal_trades'),
    path('api/review/save/', api.save_weekly_review_data, name='api_review_save'),
    path('api/outlook/current/', api.get_current_outlook, name='api_get_outlook'),
]