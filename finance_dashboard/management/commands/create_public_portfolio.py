from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from finance_dashboard.models import Portfolio, Trade
from decimal import Decimal
from datetime import date, timedelta
import random

class Command(BaseCommand):
    help = 'Create public portfolio with sample trades for demonstration'

    def handle(self, *args, **options):
        # Tạo hoặc lấy user demo
        demo_user, created = User.objects.get_or_create(
            username='demo_user',
            defaults={
                'email': 'demo@example.com',
                'first_name': 'Demo',
                'last_name': 'User'
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('Created demo user')
            )
        
        # Tạo portfolio public
        portfolio, created = Portfolio.objects.get_or_create(
            user=demo_user,
            name='Demo Portfolio',
            defaults={
                'category': 'currency',
                'symbol': 'EURUSD',
                'amount': Decimal('10000.00'),
                'is_public': True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('Created public portfolio')
            )
        else:
            # Cập nhật portfolio thành public nếu chưa
            portfolio.is_public = True
            portfolio.save()
            self.stdout.write(
                self.style.SUCCESS('Updated portfolio to public')
            )
        
        # Tạo một số trades mẫu nếu chưa có
        if not portfolio.trades.exists():
            sample_trades = [
                {
                    'symbol': 'EURUSD',
                    'side': 'BUY',
                    'entry': Decimal('1.0850'),
                    'exit': Decimal('1.0920'),
                    'stoploss': Decimal('1.0800'),
                    'qty': 10000,
                    'date': date.today() - timedelta(days=5),
                    'trade_type': 'Live',
                    'notes': 'Demo trade 1'
                },
                {
                    'symbol': 'GBPUSD',
                    'side': 'SELL',
                    'entry': Decimal('1.2650'),
                    'exit': Decimal('1.2580'),
                    'stoploss': Decimal('1.2700'),
                    'qty': 10000,
                    'date': date.today() - timedelta(days=3),
                    'trade_type': 'Live',
                    'notes': 'Demo trade 2'
                },
                {
                    'symbol': 'USDJPY',
                    'side': 'BUY',
                    'entry': Decimal('149.50'),
                    'exit': Decimal('150.20'),
                    'stoploss': Decimal('149.00'),
                    'qty': 10000,
                    'date': date.today() - timedelta(days=1),
                    'trade_type': 'Backtest',
                    'notes': 'Demo trade 3'
                }
            ]
            
            for trade_data in sample_trades:
                Trade.objects.create(
                    portfolio=portfolio,
                    **trade_data
                )
            
            self.stdout.write(
                self.style.SUCCESS(f'Created {len(sample_trades)} sample trades')
            )
        
        self.stdout.write(
            self.style.SUCCESS('Public portfolio setup completed!')
        )
