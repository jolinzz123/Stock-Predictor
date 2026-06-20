import datetime
import pickle
from pathlib import Path
from zoneinfo import ZoneInfo

CACHE_DIR = Path("cache")

_ET = ZoneInfo("America/New_York")
_MARKET_CLOSE = datetime.time(16, 0)  # 4:00 PM ET, Mon–Fri


def _path(ticker: str) -> Path:
    return CACHE_DIR / f"{ticker.upper()}.pkl"


def _cache_is_stale(mtime: float) -> bool:
    save_dt = datetime.datetime.fromtimestamp(mtime, tz=_ET)
    now_dt  = datetime.datetime.now(tz=_ET)

    check = save_dt.date()
    end   = now_dt.date()

    while check <= end:
        if check.weekday() < 5:          # Monday=0 … Friday=4
            close_dt = datetime.datetime.combine(check, _MARKET_CLOSE, tzinfo=_ET)
            if save_dt < close_dt <= now_dt:
                return True
        check += datetime.timedelta(days=1)

    return False


def load(ticker: str) -> dict | None:
    p = _path(ticker)
    if not p.exists():
        return None
    if _cache_is_stale(p.stat().st_mtime):
        return None
    with open(p, "rb") as f:
        return pickle.load(f)


def save(ticker: str, data: dict) -> None:
    CACHE_DIR.mkdir(exist_ok=True)
    with open(_path(ticker), "wb") as f:
        pickle.dump(data, f)


def cached_tickers() -> list[str]:
    if not CACHE_DIR.exists():
        return []
    return [p.stem for p in CACHE_DIR.glob("*.pkl")]
