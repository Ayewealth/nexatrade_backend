from django.core.cache import cache
import requests

COINGECKO_API_URL = "https://api.coingecko.com/api/v3"


def get_coins_list_cached():
    coins = cache.get("coingecko_coins_list")
    if coins is None:
        response = requests.get(f"{COINGECKO_API_URL}/coins/list")
        response.raise_for_status()
        coins = response.json()
        cache.set("coingecko_coins_list", coins,
                  timeout=3600)  # Cache for 1 hour
    return coins


def get_coinpaprika_coins_cached(timeout=600):
    cache_key = "coinpaprika_all_coins"
    data = cache.get(cache_key)
    if data is None:
        url = "https://api.coinpaprika.com/v1/coins"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        cache.set(cache_key, data, timeout)
    return data


def get_coinpaprika_logo(coin_id):
    """
    Fetch logo URL from CoinPaprika's coin detail endpoint.
    """
    url = f"https://api.coinpaprika.com/v1/coins/{coin_id}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("logo")
    except Exception as e:
        print(f"Failed to get logo for {coin_id}: {e}")
        return None
