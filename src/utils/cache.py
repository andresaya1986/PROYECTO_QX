import functools
from typing import Any, Callable

from cachetools import TTLCache

from src.config.settings import get_settings


def ttl_cache(maxsize: int = 256):
    """Decorador para cachear en memoria el resultado de funciones async de solo lectura.

    Pensado para envolver lecturas agregadas (metrics/reports) cuyo costo de cómputo
    supera ampliamente el costo de servir una respuesta levemente desactualizada,
    dado que la ingesta solo refresca datos cada pocos minutos.
    """

    def decorator(func: Callable) -> Callable:
        cache: TTLCache = TTLCache(maxsize=maxsize, ttl=get_settings().cache_ttl_seconds)

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = (args, tuple(sorted(kwargs.items())))
            if key in cache:
                return cache[key]
            result = await func(*args, **kwargs)
            cache[key] = result
            return result

        wrapper.cache_clear = cache.clear  # útil para tests
        return wrapper

    return decorator
