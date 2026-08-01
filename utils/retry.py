"""
Exponential backoff + jitter, buat retry request ke API eksternal
(BMKG, PetaBencana, Supabase) yang kena rate-limit (HTTP 429) atau
error transient lainnya. Lihat RFC.md § Retry utility.
"""
import asyncio
import logging
import random
from typing import Awaitable, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def with_retry(
    func: Callable[[], Awaitable[T]],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 20.0,
) -> T:
    """
    Jalankan `func` (async callable tanpa argumen — bungkus pakai lambda/closure
    kalau butuh pass argumen) dengan retry exponential backoff + jitter.

    Contoh pemakaian:
        data = await with_retry(lambda: bmkg_client.fetch_weather(kode_adm4))
    """
    attempt = 0
    while True:
        try:
            return await func()
        except Exception as exc:  # noqa: BLE001 - sengaja tangkap luas, ini boundary retry
            attempt += 1
            if attempt > max_retries:
                logger.error("Gagal setelah %s percobaan: %s", max_retries, exc)
                raise

            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            jitter = random.uniform(0, delay * 0.5)
            wait_time = delay + jitter

            logger.warning(
                "Percobaan %s/%s gagal (%s), retry dalam %.2fs",
                attempt,
                max_retries,
                exc,
                wait_time,
            )
            await asyncio.sleep(wait_time)
