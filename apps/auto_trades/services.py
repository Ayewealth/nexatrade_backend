# auto_trades/services.py (new file)
import random
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from .models import PackageSubscription, AutoTrade
from apps.trading.models import Trade, Market
import logging

logger = logging.getLogger(__name__)


class AutoTradingService:
    """Service class to handle automatic trading logic"""

    @staticmethod
    def create_auto_trade(subscription: PackageSubscription):
        """Create an automatic trade for a subscription"""
        try:
            if not subscription.should_create_new_trade():
                return None

            # Select a random market from preferred markets
            markets = subscription.package.get_preferred_markets()
            if not markets.exists():
                logger.warning(
                    f"No active markets available for subscription {subscription.id}")
                return None

            market = random.choice(markets)

            # Calculate trade amount (percentage of remaining investment)
            remaining_investment = subscription.investment_amount - \
                subscription.total_profit_earned
            min_percentage = subscription.package.min_trade_amount_percentage / 100
            max_percentage = subscription.package.max_trade_amount_percentage / 100

            trade_percentage = Decimal(
                str(random.uniform(float(min_percentage), float(max_percentage))))
            trade_amount_usd = remaining_investment * trade_percentage

            # Convert USD amount to crypto amount
            crypto_amount = trade_amount_usd / market.current_price

            # Ensure minimum trade amount
            if crypto_amount < market.min_trade_amount:
                crypto_amount = market.min_trade_amount

            # Random trade type (buy/sell)
            trade_type = random.choice(['buy', 'sell'])

            # Calculate take profit and stop loss
            take_profit, stop_loss = AutoTradingService._calculate_profit_targets(
                market.current_price, trade_type, subscription
            )

            # Create the trade
            trade = Trade.objects.create(
                user=subscription.user,
                market=market,
                trade_type=trade_type,
                amount=crypto_amount,
                price=market.current_price,
                leverage=1,  # Keep leverage at 1 for auto-trades
                take_profit=take_profit,
                stop_loss=stop_loss,
                status='open',
                profit_calculation_mode='manual'  # We'll control profit manually
            )

            # Create auto-trade record
            auto_trade = AutoTrade.objects.create(
                subscription=subscription,
                trade=trade
            )

            # Update subscription
            subscription.last_trade_time = timezone.now()
            subscription.save()

            # Schedule trade closure (simulate market movement)
            AutoTradingService._schedule_trade_closure(trade, subscription)

            logger.info(
                f"Created auto-trade {trade.id} for subscription {subscription.id}")
            return auto_trade

        except Exception as e:
            logger.error(
                f"Error creating auto-trade for subscription {subscription.id}: {str(e)}")
            return None

    @staticmethod
    def _calculate_profit_targets(current_price, trade_type, subscription):
        """Calculate take profit and stop loss levels"""
        # Random profit target between 2-8%
        profit_percentage = Decimal(str(random.uniform(0.02, 0.08)))
        # Random stop loss between 1-3%
        loss_percentage = Decimal(str(random.uniform(0.01, 0.03)))

        if trade_type == 'buy':
            take_profit = current_price * (1 + profit_percentage)
            stop_loss = current_price * (1 - loss_percentage)
        else:  # sell
            take_profit = current_price * (1 - profit_percentage)
            stop_loss = current_price * (1 + loss_percentage)

        return take_profit, stop_loss

    @staticmethod
    def _schedule_trade_closure(trade, subscription):
        """Schedule when to close the trade (simulate market movement)"""
        from django.core.cache import cache

        # Random time between 30 minutes to 6 hours
        closure_minutes = random.randint(30, 360)
        closure_time = timezone.now() + timedelta(minutes=closure_minutes)

        # Store in cache for background task processing
        cache_key = f"auto_trade_closure_{trade.id}"
        cache.set(cache_key, {
            'trade_id': trade.id,
            'subscription_id': subscription.id,
            'closure_time': closure_time.isoformat()
        }, timeout=closure_minutes * 60 + 300)  # 5 minute buffer

    @staticmethod
    def close_auto_trade(trade, subscription):
        """Close an auto-trade with calculated profit"""
        try:
            if trade.status != 'open':
                return False

            # Calculate desired profit based on package progress
            remaining_profit_needed = subscription.expected_profit - \
                subscription.total_profit_earned
            days_remaining = (subscription.end_date - timezone.now()).days
            total_days = subscription.package.duration_days

            # Calculate profit to ensure we meet expectations
            if days_remaining > 0:
                # Distribute remaining profit over remaining time
                base_profit = remaining_profit_needed / max(days_remaining, 1)
                # Add some randomness (+/- 20%)
                profit_multiplier = Decimal(str(random.uniform(0.8, 1.2)))
                trade_profit = base_profit * profit_multiplier
            else:
                # Package expired, give remaining profit needed
                trade_profit = remaining_profit_needed

            # Ensure profit is not negative (can have small losses occasionally)
            min_profit = -trade.amount * trade.price * \
                Decimal('0.02')  # Max 2% loss
            max_profit = trade.amount * trade.price * \
                Decimal('0.1')    # Max 10% profit
            trade_profit = max(min_profit, min(trade_profit, max_profit))

            # Close the trade
            trade.status = 'closed'
            trade.manual_profit = trade_profit
            trade.current_profit = trade_profit
            trade.closed_at = timezone.now()
            trade.save()

            # Update subscription profit tracking
            subscription.total_profit_earned += trade_profit
            subscription.save()

            # Return margin + profit to user's wallet (handled by existing trade close logic)
            from apps.wallets.models import USDWallet
            usd_wallet, created = USDWallet.objects.get_or_create(
                user=subscription.user,
                defaults={'balance': 0}
            )

            initial_margin = trade.amount * trade.price
            usd_wallet.balance += initial_margin + trade_profit
            usd_wallet.save()

            logger.info(
                f"Closed auto-trade {trade.id} with profit {trade_profit}")
            return True

        except Exception as e:
            logger.error(f"Error closing auto-trade {trade.id}: {str(e)}")
            return False

    @staticmethod
    def process_active_subscriptions():
        """Process all active subscriptions and create trades as needed"""
        active_subscriptions = PackageSubscription.objects.filter(
            status='active',
            is_auto_trading_active=True,
            end_date__gt=timezone.now()
        )

        created_trades = []
        for subscription in active_subscriptions:
            auto_trade = AutoTradingService.create_auto_trade(subscription)
            if auto_trade:
                created_trades.append(auto_trade)

        return created_trades
