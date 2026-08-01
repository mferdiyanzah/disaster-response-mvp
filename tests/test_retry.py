"""RT-01, RT-02: retry utility."""
import pytest

from utils.retry import with_retry


@pytest.mark.asyncio
async def test_with_retry_succeeds_after_failures():
    attempts = 0

    async def flaky():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ConnectionError("transient")
        return "ok"

    result = await with_retry(flaky, max_retries=3, base_delay=0.01, max_delay=0.05)
    assert result == "ok"
    assert attempts == 3


@pytest.mark.asyncio
async def test_with_retry_raises_after_max_retries():
    async def always_fail():
        raise ConnectionError("down")

    with pytest.raises(ConnectionError):
        await with_retry(always_fail, max_retries=2, base_delay=0.01, max_delay=0.05)
