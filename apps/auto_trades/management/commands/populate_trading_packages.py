# apps/auto_trades/management/commands/populate_trading_packages.py
from django.core.management.base import BaseCommand
import json


class Command(BaseCommand):
    help = 'Populate trading packages'

    def handle(self, *args, **options):
        from apps.auto_trades.models import TradingPackage
        
        TRADING_PACKAGES = [
            {
                'name': 'Conservative Growth',
                'description': 'Low-risk auto-trading package perfect for beginners. Focuses on stable, established cryptocurrencies with proven track records. Ideal for users who prefer steady, predictable returns over high-risk investments.',
                'min_investment': 100.00,
                'max_investment': 5000.00,
                'duration_days': 30,
                'profit_percentage': 8.50,
                'risk_level': 'Low',
                'features': [
                    'Focus on top 10 cryptocurrencies',
                    'Conservative position sizing',
                    'Stop-loss protection',
                    'Daily performance reports',
                    'Risk management alerts'
                ],
                'max_trades_per_day': 3,
                'min_trade_amount_percentage': 5.00,
                'max_trade_amount_percentage': 15.00,
                'trade_frequency_hours': 8,
                'is_active': True
            },
            {
                'name': 'Balanced Portfolio',
                'description': 'Medium-risk package that balances growth potential with risk management. Trades across major and mid-cap cryptocurrencies using technical analysis and market trends. Perfect for investors seeking moderate returns.',
                'min_investment': 500.00,
                'max_investment': 15000.00,
                'duration_days': 45,
                'profit_percentage': 18.75,
                'risk_level': 'Medium',
                'features': [
                    'Diversified crypto portfolio',
                    'Technical analysis integration',
                    'Market trend following',
                    'Automated rebalancing',
                    'Weekly strategy updates',
                    'Risk-adjusted position sizing'
                ],
                'max_trades_per_day': 5,
                'min_trade_amount_percentage': 8.00,
                'max_trade_amount_percentage': 25.00,
                'trade_frequency_hours': 6,
                'is_active': True
            },
            {
                'name': 'Aggressive Growth',
                'description': 'High-risk, high-reward package for experienced traders. Utilizes advanced trading strategies, leverages market volatility, and includes emerging cryptocurrencies. Designed for maximum profit potential.',
                'min_investment': 1000.00,
                'max_investment': 50000.00,
                'duration_days': 60,
                'profit_percentage': 35.00,
                'risk_level': 'High',
                'features': [
                    'Advanced algorithmic trading',
                    'High-frequency trading capabilities',
                    'Emerging altcoin opportunities',
                    'Volatility-based strategies',
                    'Real-time market analysis',
                    'Dynamic risk management',
                    'Priority execution speeds'
                ],
                'max_trades_per_day': 8,
                'min_trade_amount_percentage': 10.00,
                'max_trade_amount_percentage': 35.00,
                'trade_frequency_hours': 4,
                'is_active': True
            },
            {
                'name': 'Premium Elite',
                'description': 'Exclusive package for high-net-worth investors. Combines institutional-grade strategies with personalized portfolio management. Includes access to premium markets, advanced analytics, and dedicated support.',
                'min_investment': 10000.00,
                'max_investment': 250000.00,
                'duration_days': 90,
                'profit_percentage': 55.00,
                'risk_level': 'Premium',
                'features': [
                    'Institutional-grade algorithms',
                    'Multi-exchange arbitrage',
                    'Personalized strategy optimization',
                    'Premium market access',
                    'Dedicated account manager',
                    'Custom risk parameters',
                    'Advanced analytics dashboard',
                    'Priority customer support',
                    'Exclusive trading signals'
                ],
                'max_trades_per_day': 12,
                'min_trade_amount_percentage': 12.00,
                'max_trade_amount_percentage': 40.00,
                'trade_frequency_hours': 3,
                'is_active': True
            }
        ]

        for package_data in TRADING_PACKAGES:
            features = package_data.pop('features')
            package, created = TradingPackage.objects.get_or_create(
                name=package_data['name'],
                defaults=package_data
            )
            if created:
                package.set_features(features)
                package.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created package: {package.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'• Package already exists: {package.name}')
                )

        self.stdout.write(
            self.style.SUCCESS('Successfully populated trading packages!')
        )
