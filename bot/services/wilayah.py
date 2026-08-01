"""
Lookup kode wilayah administratif Indonesia, buat mapping input teks bebas
user (nama kecamatan/kota) ke kode adm4 yang dibutuhkan API BMKG.

Sumber: emsifa/api-wilayah-indonesia (statis, hosted di GitHub Pages →
redirect ke www.emsifa.com). Data di-cache penuh di memori.
"""
import asyncio
import logging

import httpx

from bot import config
from bot.services import bmkg

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(10.0)

# Base URL langsung ke redirect target supaya skip 301 hop
_DIRECT_BASE = "http://www.emsifa.com/api-wilayah-indonesia/api"

_provinces_cache: list[dict] | None = None
_regencies_cache: list[dict] | None = None
_districts_cache: list[dict] | None = None

_NAME_PREFIXES = (
    "kecamatan ",
    "kelurahan ",
    "desa ",
    "kec. ",
    "kel. ",
    "kec ",
    "kel ",
)


async def get_provinces() -> list[dict]:
    global _provinces_cache
    if _provinces_cache is not None:
        return _provinces_cache

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.get(f"{_DIRECT_BASE}/provinces.json")
        resp.raise_for_status()
        _provinces_cache = resp.json()
        return _provinces_cache


async def get_all_regencies() -> list[dict]:
    """Fetch semua kab/kota secara concurrent (cached setelah pertama kali)."""
    global _regencies_cache
    if _regencies_cache is not None:
        return _regencies_cache

    provinces = await get_provinces()

    async def _fetch_one(client: httpx.AsyncClient, prov: dict) -> list[dict]:
        try:
            resp = await client.get(f"{_DIRECT_BASE}/regencies/{prov['id']}.json")
            resp.raise_for_status()
            regencies = resp.json()
            for r in regencies:
                r["province_id"] = prov["id"]
            return regencies
        except Exception:
            logger.warning("Gagal fetch regencies untuk province %s", prov["id"])
            return []

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        results = await asyncio.gather(
            *[_fetch_one(client, p) for p in provinces]
        )

    all_regencies = []
    for batch in results:
        all_regencies.extend(batch)

    _regencies_cache = all_regencies
    return _regencies_cache


async def get_regencies(province_id: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.get(f"{_DIRECT_BASE}/regencies/{province_id}.json")
        resp.raise_for_status()
        return resp.json()


async def get_districts(regency_id: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.get(f"{_DIRECT_BASE}/districts/{regency_id}.json")
        resp.raise_for_status()
        return resp.json()


async def get_all_districts() -> list[dict]:
    """Lazy-load semua kecamatan (~7000) — cached setelah pertama kali."""
    global _districts_cache
    if _districts_cache is not None:
        return _districts_cache

    regencies = await get_all_regencies()

    async def _fetch_one(client: httpx.AsyncClient, regency: dict) -> list[dict]:
        try:
            resp = await client.get(f"{_DIRECT_BASE}/districts/{regency['id']}.json")
            resp.raise_for_status()
            districts = resp.json()
            for d in districts:
                d["regency_id"] = regency["id"]
            return districts
        except Exception:
            logger.warning("Gagal fetch districts untuk regency %s", regency["id"])
            return []

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        results = await asyncio.gather(
            *[_fetch_one(client, r) for r in regencies]
        )

    all_districts: list[dict] = []
    for batch in results:
        all_districts.extend(batch)

    _districts_cache = all_districts
    return _districts_cache


async def get_villages(district_id: str) -> list[dict]:
    """Level ke-4 (kelurahan/desa) — id di sini yang dipakai sebagai kode adm4."""
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.get(f"{_DIRECT_BASE}/villages/{district_id}.json")
        resp.raise_for_status()
        return resp.json()


async def resolve_adm4_for_bmkg(district_id: str) -> str | None:
    """Resolve district ID ke kode adm4 BMKG via first village."""
    villages = await get_villages(district_id)
    if not villages:
        return None
    return bmkg.format_adm4_for_bmkg(villages[0]["id"])


def normalize_name(name: str) -> str:
    """Lowercase + buang prefix administratif umum."""
    normalized = name.strip().lower()
    for prefix in _NAME_PREFIXES:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):]
    return normalized.strip()


def find_best_match(name: str, candidates: list[dict]) -> dict | None:
    """Exact match lalu substring, pakai normalize_name."""
    query = normalize_name(name)
    if not query:
        return None

    for c in candidates:
        if normalize_name(c["name"]) == query:
            return c
    for c in candidates:
        candidate = normalize_name(c["name"])
        if query in candidate or candidate in query:
            return c
    return None


async def match_nominatim_to_emsifa(nominatim_data: dict) -> dict | None:
    """Map hasil Nominatim ke district Emsifa, atau None."""
    addr = nominatim_data.get("address", {})
    district_names: list[str] = []
    for key in ("suburb", "village", "neighbourhood", "city_district", "town", "hamlet"):
        val = addr.get(key)
        if val and val not in district_names:
            district_names.append(val)

    if not district_names:
        return None

    districts = await get_all_districts()
    for name in district_names:
        match = find_best_match(name, districts)
        if match:
            return match

    return None


async def smart_search(query: str) -> tuple[str, dict] | None:
    """
    Cari query di province, regency, atau district.
    Return (level, item) atau None. level: province | regency | district
    """
    provinces = await get_provinces()
    match = find_best_match(query, provinces)
    if match:
        return ("province", match)

    regencies = await get_all_regencies()
    match = find_best_match(query, regencies)
    if match:
        return ("regency", match)

    districts = await get_all_districts()
    match = find_best_match(query, districts)
    if match:
        return ("district", match)

    return None
