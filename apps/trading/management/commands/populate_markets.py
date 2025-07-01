import time
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.core.cache import cache
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from apps.wallets.models import CryptoType
from apps.trading.models import Market
from apps.trading.utils import get_market_tickers_cached, get_coinpaprika_tickers_cached


class Command(BaseCommand):
    help = "Populate Market data using CoinPaprika (batch) and fallback to CoinGecko"

    def handle(self, *args, **kwargs):
        channel_layer = get_channel_layer()
        total_markets_created = 0
        total_markets_updated = 0

        # Fetch and index CoinPaprika data
        paprika_data = get_coinpaprika_tickers_cached()
        paprika_index = {item['symbol'].upper(): item for item in paprika_data}

        active_cryptos = CryptoType.objects.filter(is_active=True)
        total = active_cryptos.count()

        for idx, crypto in enumerate(active_cryptos, start=1):
            self.stdout.write(
                f"[{idx}/{total}] Fetching markets for {crypto.symbol}...")

            symbol = crypto.symbol.upper()
            used_paprika = False

            tickers = []

            if symbol in paprika_index:
                used_paprika = True
                item = paprika_index[symbol]
                quotes = item.get('quotes', {})

                # Simulate tickers as CoinGecko format for consistency
                for quote_symbol, quote_data in quotes.items():
                    tickers.append({
                        'target': quote_symbol,
                        'last': quote_data['price']
                    })

            else:
                # fallback to CoinGecko
                coingecko_id = crypto.coingecko_id
                if not coingecko_id:
                    self.stdout.write(self.style.WARNING(
                        f"No CoinGecko ID for {crypto.symbol} — skipping."))
                    continue

                try:
                    data = get_market_tickers_cached(coingecko_id)
                    tickers = data.get('tickers', [])
                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f"Failed to fetch from CoinGecko for {crypto.symbol}: {e}"))
                    continue

            existing_market_names = set(Market.objects.filter(
                base_currency=crypto).values_list('name', flat=True))
            current_market_names = set()

            for ticker in tickers:
                try:
                    base = crypto.symbol.upper()
                    quote = ticker['target'].upper()
                    market_name = f"{base}/{quote}"

                    current_price = Decimal(ticker['last'])
                    min_trade_amount = Decimal('0.001')

                    market, created = Market.objects.update_or_create(
                        name=market_name,
                        base_currency=crypto,
                        defaults={
                            'quote_currency': quote,
                            'current_price': current_price,
                            'min_trade_amount': min_trade_amount,
                            'is_active': True,
                        }
                    )

                    current_market_names.add(market_name)

                    if created:
                        total_markets_created += 1
                    else:
                        total_markets_updated += 1

                    async_to_sync(channel_layer.group_send)(
                        "markets",
                        {
                            "type": "market_update",
                            "data": {
                                "market": market.name,
                                "price": str(market.current_price),
                                "symbol": market.base_currency.symbol,
                            },
                        }
                    )
                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f"Error processing ticker for {crypto.symbol}: {e}"
                    ))

            # Deactivate stale markets
            Market.objects.filter(name__in=(existing_market_names - current_market_names),
                                  base_currency=crypto).update(is_active=False)

            time.sleep(1)  # gentle throttle

        self.stdout.write(self.style.SUCCESS(
            f"Markets created: {total_markets_created}, updated: {total_markets_updated}"
        ))
