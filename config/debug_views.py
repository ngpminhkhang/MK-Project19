# config/debug_views.py
from django.http import HttpResponse
from django.conf import settings
import os

def debug_cloudinary(request):
    """Kiểm tra Cloudinary config"""
    html = "<h1>🔧 Cloudinary Debug</h1>"
    
    html += "<h2>Environment Variables</h2>"
    html += f"<p>CLOUD_NAME: {os.environ.get('CLOUDINARY_CLOUD_NAME', '❌ MISSING')}</p>"
    html += f"<p>API_KEY: {os.environ.get('CLOUDINARY_API_KEY', '❌ MISSING')}</p>"
    html += f"<p>API_SECRET: {'*' * len(os.environ.get('CLOUDINARY_API_SECRET', ''))}</p>"
    
    html += "<h2>Django Settings</h2>"
    html += f"<p>DEFAULT_FILE_STORAGE: {getattr(settings, 'DEFAULT_FILE_STORAGE', '❌ Not set')}</p>"
    
    cloudinary_apps = [app for app in settings.INSTALLED_APPS if 'cloudinary' in app]
    html += f"<p>Cloudinary apps: {cloudinary_apps}</p>"
    
    if hasattr(settings, 'MEDIA_ROOT'):
        html += f"<p>⚠️ MEDIA_ROOT: {settings.MEDIA_ROOT} - Đang dùng LOCAL storage</p>"
    else:
        html += "<p>✅ Không có MEDIA_ROOT - Có thể đang dùng Cloudinary</p>"
    
    # Kiểm tra config
    cloudinary_configured = all([
        os.environ.get('CLOUDINARY_CLOUD_NAME'),
        os.environ.get('CLOUDINARY_API_KEY'), 
        os.environ.get('CLOUDINARY_API_SECRET')
    ])
    
    html += "<h2>Kết luận</h2>"
    if cloudinary_configured:
        html += "<p style='color: green;'>✅ Cloudinary environment variables: ĐẦY ĐỦ</p>"
    else:
        html += "<p style='color: red;'>❌ Cloudinary environment variables: THIẾU</p>"
    
    if 'cloudinary_storage' in settings.INSTALLED_APPS:
        html += "<p style='color: green;'>✅ Cloudinary apps: ĐÃ CÀI ĐẶT</p>"
    else:
        html += "<p style='color: red;'>❌ Cloudinary apps: CHƯA CÀI ĐẶT</p>"
    
    return HttpResponse(html)

def debug_database(request):
    """Kiểm tra database và public portfolios"""
    from finance_dashboard.models import Portfolio, Trade
    from django.contrib.auth.models import User
    
    html = "<h1>🗃 Database Debug</h1>"
    
    html += "<h2>Tổng quan</h2>"
    html += f"<p>Total Users: {User.objects.count()}</p>"
    html += f"<p>Total Portfolios: {Portfolio.objects.count()}</p>"
    html += f"<p>Total Trades: {Trade.objects.count()}</p>"
    
    html += "<h2>Public Portfolios</h2>"
    public_portfolios = Portfolio.objects.filter(is_public=True)
    html += f"<p>Số portfolio public: {public_portfolios.count()}</p>"
    
    for portfolio in public_portfolios:
        trades = portfolio.trades.all()
        html += f"<h3>📁 {portfolio.name} (user: {portfolio.user})</h3>"
        html += f"<p>Số trades: {trades.count()}</p>"
        for trade in trades[:5]:  # Hiển thị 5 trades đầu
            html += f"<p>• {trade.symbol} - {trade.side} - {trade.date}</p>"
    
    html += "<h2>Tất cả Portfolios</h2>"
    all_portfolios = Portfolio.objects.all().select_related('user')
    for portfolio in all_portfolios:
        html += f"<p>'{portfolio.name}' (public: {portfolio.is_public}, user: {portfolio.user.username}): {portfolio.trades.count()} trades</p>"
    
    html += "<h2>Kết luận</h2>"
    if public_portfolios.exists():
        html += "<p style='color: green;'>✅ Có portfolio public - Khách nên thấy được</p>"
    else:
        html += "<p style='color: red;'>❌ Không có portfolio public - Khách sẽ không thấy gì</p>"
        html += "<p>💡 Cần tạo portfolio với is_public=True</p>"
    
    return HttpResponse(html)

def test_upload(request):
    """Test upload file lên Cloudinary"""
    from finance_dashboard.models import Insight
    from django.core.files.uploadedfile import SimpleUploadedFile
    
    html = "<h1>📤 Test Cloudinary Upload</h1>"
    
    if request.method == 'POST' and request.FILES.get('test_file'):
        try:
            # Tạo insight test
            insight = Insight(
                title="Test Upload - " + str(request.FILES['test_file'].name),
                summary="Test file upload to Cloudinary",
                category="other",
                result="neutral"
            )
            
            # Lưu file
            insight.attached_image = request.FILES['test_file']
            insight.save()
            
            html += f"<p style='color: green;'>✅ Upload THÀNH CÔNG!</p>"
            html += f"<p>File URL: {insight.attached_image.url}</p>"
            html += f"<p>File name: {insight.attached_image.name}</p>"
            
            # Kiểm tra xem có phải Cloudinary URL không
            if 'cloudinary.com' in insight.attached_image.url:
                html += f"<p style='color: green;'>✅ Đang dùng CLOUDINARY storage</p>"
            else:
                html += f"<p style='color: red;'>❌ Vẫn dùng LOCAL storage</p>"
                
        except Exception as e:
            html += f"<p style='color: red;'>❌ Upload THẤT BẠI: {e}</p>"
    
    # Form upload test
    html += """
    <form method="post" enctype="multipart/form-data">
        <input type="file" name="test_file" required>
        <button type="submit">Upload Test File</button>
    </form>
    <p><small>Upload 1 file ảnh nhỏ để test</small></p>
    """
    
    return HttpResponse(html)

def fix_public_data(request):
    """Chuyển trades sang portfolio public"""
    from finance_dashboard.models import Portfolio
    
    html = "<h1>🔧 Fix Public Data</h1>"
    
    # Lấy portfolio có trades
    currency_portfolio = Portfolio.objects.get(name="Currency")
    demo_portfolio = Portfolio.objects.get(name="Demo Portfolio")
    
    # Đổi currency thành public
    currency_portfolio.is_public = True
    currency_portfolio.save()
    
    # Đổi demo thành private (tùy chọn)
    demo_portfolio.is_public = False  
    demo_portfolio.save()
    
    html += f"<p>✅ Đã đổi '{currency_portfolio.name}' thành public</p>"
    html += f"<p>✅ Đã đổi '{demo_portfolio.name}' thành private</p>"
    html += f"<p>Bây giờ khách sẽ thấy: {currency_portfolio.trades.count()} trades</p>"
    
    return HttpResponse(html)

def fix_public_data(request):
    """Chuyển portfolio có trades thành public"""
    from finance_dashboard.models import Portfolio
    
    html = "<h1>🔧 Fix Public Portfolio Data</h1>"
    
    try:
        # Lấy portfolio có trades
        currency_portfolio = Portfolio.objects.get(name="Currency")
        demo_portfolio = Portfolio.objects.get(name="Demo Portfolio")
        
        # Đổi currency thành public (có trades)
        currency_portfolio.is_public = True
        currency_portfolio.save()
        
        # Đổi demo thành private (không có trades)
        demo_portfolio.is_public = False  
        demo_portfolio.save()
        
        html += f"<p style='color: green;'>✅ Đã đổi '{currency_portfolio.name}' thành PUBLIC</p>"
        html += f"<p style='color: green;'>✅ Đã đổi '{demo_portfolio.name}' thành PRIVATE</p>"
        html += f"<p>Bây giờ khách sẽ thấy: {currency_portfolio.trades.count()} trades</p>"
        
    except Exception as e:
        html += f"<p style='color: red;'>❌ Lỗi: {e}</p>"
    
    return HttpResponse(html)