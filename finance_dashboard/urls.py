from django.urls import path, include
from . import views
from . import api
from django.contrib.auth.views import LoginView

urlpatterns = [
    # Auth
    path('login/', LoginView.as_view(template_name='finance_dashboard/login.html'), name='login'),
    
    # Main pages
    path("", views.home, name='home'),
    path("analysis/", views.analysis, name="analysis"),
    path("analysis/ajax/", views.analysis_ajax, name="analysis_ajax"),
    path("portfolio/", views.portfolio, name="portfolio"),
    path("about/", views.about, name="about"),
    path('search/', views.search_view, name='search'),
    path('chart/<str:symbol>/', views.chart_view, name='chart'),
    path("details/<str:symbol>/", views.details, name="details"),
    
    # Insights CRUD
    path("insights/", views.insights, name="insights"),
    path("insight/create/", views.create_insight, name="create_insight"),
    path("insight/create/<int:portfolio_id>/", views.create_insight_for_portfolio, name="create_insight_for_portfolio"),
    path("insight/edit/<int:insight_id>/", views.edit_insight, name="edit_insight"),
    path("insight/delete/<int:insight_id>/", views.delete_insight, name="delete_insight"),
    path("insight/search/", views.search_insights, name="search_insights"),
    path("insight/modal/<int:pk>/", views.insight_modal, name="insight_modal"),
    path("insight/<int:pk>/", views.insight_modal, name="insight_model"),
    
    # Trade insight creation
    path("trade/create-insight/", views.create_insight_from_trade, name="create_insight_from_trade"),
    path("portfolio/<int:portfolio_id>/create-insight/", views.create_insight_for_portfolio, name="create_insight_for_portfolio"),
    path("trade/<int:trade_id>/insight/", views.trade_insight_modal, name="trade_insight_modal"),
    path("trade/<int:trade_id>/edit/", views.edit_trade, name="edit_trade"),
    path("trade/<int:trade_id>/delete/", views.delete_trade, name="delete_trade"),
    path("trades/filter/<str:trade_type>/", views.filter_trades, name="filter_trades"),
    path("get-symbol-choices/", views.get_symbol_choices, name="get_symbol_choices"),

    # ==========================================
    # PHẦN 1: AUM TERMINAL
    # ==========================================
    path("api/portfolio/metrics/", api.get_portfolio_metrics, name="api_get_portfolio_metrics"),
    path("api/portfolio/mode/", api.update_portfolio_mode, name="api_update_portfolio_mode"),
    path("api/portfolio/rebalance/", api.apply_portfolio_rebalance, name="api_apply_portfolio_rebalance"),
    path("api/portfolio/analytics/", api.get_performance_analytics, name="api_get_performance_analytics"),
    path("api/dashboard/stats/", api.get_dashboard_stats, name="api_get_dashboard_stats"),

    # ==========================================
    # PHẦN 2: SIGNAL ENGINE & SCENARIOS
    # ==========================================
    path("api/settings/", api.get_app_settings, name="api_get_app_settings"),
    path("api/portfolio/state/", api.get_portfolio_state, name="api_get_portfolio_state"),
    path("api/scenarios/", api.get_scenarios, name="api_get_scenarios"),
    path("api/scenarios/create/", api.create_scenario, name="api_create_scenario"),
    
    # [VÙNG LÕI ĐÃ ĐƯỢC BỌC THÉP] Đưa luồng cập nhật về hàm views.update_scenario_api xịn xò
    path("api/scenarios/update/", views.update_scenario_api, name="api_update_scenario_full"),
    
    path("api/scenarios/status/", api.set_scenario_status, name="api_set_scenario_status"),
    path("api/scenarios/delete/", api.delete_scenario, name="api_delete_scenario"),
    path("api/scenarios/execute/", api.execute_trade, name="api_execute_trade"),

    # PHẦN 3: MARKET MONITOR
    path("api/webhook/signal/", api.webhook_mt5_signal, name="api_webhook_signal"),
    path("api/monitor/signals/", api.get_live_signals, name="api_get_live_signals"),

    # PHẦN 4: MT5 TICKET MASTER BRIDGE
    path("api/bridge/pending/", api.bridge_get_pending_order, name="api_bridge_get_pending"),
    path("api/bridge/confirm/", api.bridge_confirm_execution, name="api_bridge_confirm"),
    path("api/bridge/closed/", api.bridge_report_closed_trade, name="api_bridge_closed"),
    path("api/bridge/sync_pnl/", api.bridge_sync_live_pnl, name="api_bridge_sync_pnl"),

    # PHẦN 5: TRADE JOURNAL
    path("api/journal/trades/", api.get_journal_trades, name="api_journal_trades"),
    path("api/journal/update/", api.update_journal_review, name="api_journal_update"),

    # PHẦN 6: WEEKLY REVIEW
    path("api/review/data/", api.get_weekly_review_data, name="api_review_data"),
    path("api/review/save/", api.save_weekly_review_data, name="api_review_save"),
    path("api/review/missed/", api.handle_missed_trades, name="api_review_missed"),
    
    # [VÙNG LÕI ĐÃ ĐƯỢC BỌC THÉP] Đưa luồng review về views.review_api
    path('api/reviews/', views.review_api, name='api_reviews'),

    # PHẦN 7: MONITOR
    path("api/monitor/active/", api.get_active_trades, name="api_monitor_active"),
    path("api/monitor/kill/", api.kill_switch_trade, name="api_monitor_kill"),
    path("api/bridge/closes/", api.bridge_pending_closes, name="api_bridge_closes"),

    # PHẦN 8: LIBRARY
    path("api/library/", api.manage_system_library, name="api_library_manage"),

    # PHẦN 9: CONFIG & STATE
    path("api/config/state/", api.manage_system_config, name="api_config_state"),
    path("api/settings/", api.get_settings, name="api_settings_old"),

    # PART 10: DASHBOARD
    path("api/dashboard/metrics/", api.get_dashboard_metrics, name="api_dashboard_metrics"),
    
    # ==========================================
    # CÁC API ENDPOINT MẶT TIỀN KHÁC (VIEWS)
    # ==========================================
    path('api/config/state/legacy/', views.config_state_api, name='api_config_state_legacy'),
    path('api/dashboard/metrics/legacy/', views.dashboard_metrics_api, name='api_dashboard_metrics_legacy'),

    path('api/mt5/execution/', views.mt5_execution_node, name='api_mt5_execution'),
    
    path('api/mt5/check_status/', views.check_ticket_status, name='api_check_status'),
    path('api/mt5/approve/', views.approve_ticket_api, name='api_approve_ticket'),
    
    path('api/mt5/fetch_approved/', views.get_approved_tickets, name='api_fetch_approved'),
    path('api/mt5/mark_executed/', views.mark_executed, name='api_mark_executed'),
    path('api/outlook/sync/', views.sync_outlook_api, name='api_sync_outlook'),
    
    # [VÙNG LÕI ĐÃ ĐƯỢC BỌC THÉP] Ống nước an toàn cho tab FUSION
    path('api/outlook/current/', api.get_current_outlook, name='api_get_outlook'),

    path('api/mt5/direct_fire/', views.direct_fire_api, name='api_direct_fire'),

    path('api/mt5/close_trade/', views.close_trade_api, name='api_close_trade'),
    path('api/mt5/fetch_close/', views.fetch_close_commands, name='api_fetch_close'),
    path('api/mt5/mark_closed/', views.mark_closed_api, name='api_mark_closed'),

    path('api/mt5/update_pnl/', views.update_pnl_api, name='api_update_pnl'),

    path('api/mt5/radar_blip/', views.radar_blip_api, name='radar_blip_api'),
    path('api/mt5/radar_v2/', views.radar_list_api, name='radar_list_api'),
    
]