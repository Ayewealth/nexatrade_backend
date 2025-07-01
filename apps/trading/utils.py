from django.core.cache import cache
import requests


def get_market_tickers_cached(coingecko_id, timeout=600):  # cache for 10 minutes
    cache_key = f"coingecko_tickers_{coingecko_id}"
    data = cache.get(cache_key)
    if data is None:
        url = f"https://api.coingecko.com/api/v3/coins/{coingecko_id}/tickers"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        cache.set(cache_key, data, timeout=timeout)
    return data


def get_paprika_tickers_cached(coinpaprika_id, timeout=600):  # cache for 10 minutes
    cache_key = f"coinpaprika_tickers_{coinpaprika_id}"
    data = cache.get(cache_key)
    if data is None:
        url = f"https://api.coinpaprika.com/v1/tickers/{coinpaprika_id}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        cache.set(cache_key, data, timeout=timeout)
    return data


def get_coinpaprika_tickers_cached(timeout=600):
    cache_key = "coinpaprika_all_tickers"
    data = cache.get(cache_key)
    if data is None:
        url = "https://api.coinpaprika.com/v1/tickers"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        cache.set(cache_key, data, timeout=timeout)
    return data
