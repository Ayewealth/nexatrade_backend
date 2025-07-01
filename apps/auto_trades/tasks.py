# auto_trades/tasks.py (new file for Celery tasks)
from celery import shared_task
from django.core.cache import cache
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from django.utils import timezone
from .services import AutoTradingService
from .models import PackageSubscription, AutoTrade
from apps.trading.models import Trade
import logging
import json

logger = logging.getLogger(__name__)


@shared_task
def create_auto_trades():
    """Periodic task to create auto-trades for active subscriptions"""
    try:
        created_trades = AutoTradingService.process_active_subscriptions()
        logger.info(f"Created {len(created_trades)} auto-trades")
        return len(created_trades)
    except Exception as e:
        logger.error(f"Error in create_auto_trades task: {str(e)}")
        return 0


def create_auto_trades_task():
    schedule, _ = IntervalSchedule.objects.get_or_create(
        every=1,
        period=IntervalSchedule.HOURS
    )

    PeriodicTask.objects.update_or_create(
        name='Create Auto Trades Every Hour',
        defaults={
            'interval': schedule,
            'task': 'apps.auto_trades.tasks.create_auto_trades',
            'args': json.dumps([]),
        }
    )


@shared_task
def close_scheduled_auto_trades():
    """Close auto-trades that are scheduled for closure"""
    try:
        # Get all open auto-trades
        open_auto_trades = AutoTrade.objects.filter(
            trade__status='open'
        ).select_related('trade', 'subscription')

        closed_count = 0
        for auto_trade in open_auto_trades:
            cache_key = f"auto_trade_closure_{auto_trade.trade.id}"
            closure_data = cache.get(cache_key)

            if closure_data:
                closure_time = timezone.datetime.fromisoformat(
                    closure_data['closure_time'])
                if timezone.now() >= closure_time:
                    success = AutoTradingService.close_auto_trade(
                        auto_trade.trade,
                        auto_trade.subscription
                    )
                    if success:
                        closed_count += 1
                        cache.delete(cache_key)

        logger.info(f"Closed {closed_count} scheduled auto-trades")
        return closed_count

    except Exception as e:
        logger.error(f"Error in close_scheduled_auto_trades task: {str(e)}")
        return 0


def close_scheduled_auto_trades_task():
    schedule, _ = IntervalSchedule.objects.get_or_create(
        every=5,
        period=IntervalSchedule.MINUTES
    )

    PeriodicTask.objects.update_or_create(
        name='Close Scheduled Auto Trades 5 Minute',
        defaults={
            'interval': schedule,
            'task': 'apps.auto_trades.tasks.close_scheduled_auto_trades',
            'args': json.dumps([]),
        }
    )


@shared_task
def finalize_expired_subscriptions():
    """Finalize subscriptions that have expired"""
    try:
        expired_subscriptions = PackageSubscription.objects.filter(
            status='active',
            end_date__lt=timezone.now()
        )

        finalized_count = 0
        for subscription in expired_subscriptions:
            # Close any remaining open trades
            open_trades = Trade.objects.filter(
                user=subscription.user,
                status='open',
                auto_trade_info__subscription=subscription
            )

            for trade in open_trades:
                AutoTradingService.close_auto_trade(trade, subscription)

            # Mark subscription as completed
            subscription.status = 'completed'
            subscription.is_auto_trading_active = False
            subscription.save()

            finalized_count += 1

        logger.info(f"Finalized {finalized_count} expired subscriptions")
        return finalized_count

    except Exception as e:
        logger.error(f"Error in finalize_expired_subscriptions task: {str(e)}")
        return 0


def finalize_expired_subscriptions_task():
    schedule, _ = IntervalSchedule.objects.get_or_create(
        every=1,
        period=IntervalSchedule.HOURS
    )

    PeriodicTask.objects.update_or_create(
        name='Finalize Expired Subscriptions Every Hour',
        defaults={
            'interval': schedule,
            'task': 'apps.auto_trades.tasks.finalize_expired_subscriptions',
            'args': json.dumps([]),
        }
    )
