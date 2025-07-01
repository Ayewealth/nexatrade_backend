# trading/tasks.py
from celery import shared_task
from django.core.management import call_command
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from decimal import Decimal
from apps.trading.models import Market

import requests
import json
import logging

logger = logging.getLogger(__name__)


@shared_task
def update_trade_profits_task():
    """ 
    Celery task to update trade profits
    """
    try:
        call_command('update_trade_profits')
        logger.info("Trade profits updated successfully")
        return "Trade profits updated successfully"
    except Exception as e:
        logger.error(f"Error updating trade profits: {str(e)}")
        raise e


@shared_task
def test_task():
    """
    Simple test task
    """
    return "Test task completed successfully"


def create_or_update_profit_task():
    """
    Ensures a periodic task is created to run every 1 minute.
    """
    schedule, _ = IntervalSchedule.objects.get_or_create(
        every=1,
        period=IntervalSchedule.MINUTES
    )

    PeriodicTask.objects.update_or_create(
        name='Update Trade Profits Every Minute',
        defaults={
            'interval': schedule,
            'task': 'apps.trading.tasks.update_trade_profits_task',
            'args': json.dumps([]),
        }
    )


@shared_task
def update_market_prices_task():
    """
    Celery task to update market prices using CoinPaprika via management command.
    """
    try:
        call_command('update_market_prices')
        logger.info("Market prices updated successfully.")
        return "Market prices updated successfully."
    except Exception as e:
        logger.error(f"Error updating market prices: {str(e)}")
        raise e


def create_or_update_market_price_task():
    """
    Ensures a periodic task is created to update market prices every 5 minutes.
    """
    schedule, _ = IntervalSchedule.objects.get_or_create(
        every=5,  # Adjust frequency as needed
        period=IntervalSchedule.MINUTES
    )

    PeriodicTask.objects.update_or_create(
        name='Update Market Prices Every 5 Minute',
        defaults={
            'interval': schedule,
            'task': 'apps.trading.tasks.update_market_prices_task',
            'args': json.dumps([]),
        }
    )
