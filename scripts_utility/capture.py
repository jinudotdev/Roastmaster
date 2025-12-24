from dataclasses import asdict
from datetime import datetime
from typing import Dict, Any, Optional, Callable, TypeAlias
from scripts_utility.schema import RoastSession
from scripts_main.capture_roast_session import capture_roast_session

# Type alias for clarity
SessionDict: TypeAlias = Dict[str, Any]

# --- Object Creators ---
def create_roast_session(**kwargs) -> RoastSession:
    return RoastSession(**kwargs)

def log_roast(session_kwargs: SessionDict, sensory_kwargs: SessionDict) -> None:
    full_kwargs = {**session_kwargs, **sensory_kwargs}
    session = create_roast_session(**full_kwargs)
    # Convert dataclass → dict only at the persistence boundary
    capture_roast_session(asdict(session))

# --- Input Utilities ---
def parse_date_flexible(date_str: str) -> datetime:
    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            dt = datetime.strptime(date_str, fmt)
            if dt.year < 2000:
                dt = dt.replace(year=dt.year + 2000 if dt.year < 100 else dt.year)
            return dt
        except ValueError:
            continue
    raise ValueError(
        f"Unrecognized date format: {date_str}. "
        "Try MM/DD/YYYY, MM/DD/YY, or YYYY-MM-DD."
    )

def get_validated_date(prompt: str, allow_blank: bool = False) -> Optional[datetime]:
    while True:
        s = input(prompt).strip()
        if not s and allow_blank:
            return None
        try:
            return parse_date_flexible(s)
        except ValueError as e:
            print(f"⚠️ {e}")

def mmss_to_seconds(mmss: str) -> int:
    s = mmss.strip()
    if not s.isdigit() or len(s) != 4:
        raise ValueError("Time must be 4 digits in MMSS format (e.g., 0930).")
    val = int(s)
    mm = val // 100
    ss = val % 100
    if ss >= 60:
        raise ValueError("Seconds must be < 60 (e.g., 0959 is max).")
    return mm * 60 + ss

def seconds_to_mmss(seconds: Optional[float]) -> str:
    if seconds is None:
        return "n/a"
    try:
        total_seconds = int(round(float(seconds)))
    except (ValueError, TypeError):
        return "n/a"
    minutes = total_seconds // 60
    secs = total_seconds % 60
    return f"{minutes:02d}:{secs:02d}"

def get_valid_time(prompt: str) -> int:
    """Prompt until a valid 4-digit MMSS time is entered (required)."""
    while True:
        raw = input(prompt).strip()
        if not raw:
            print("⚠️ This field is required. Please enter a time in MMSS format (e.g., 0930).")
            continue
        if raw.isdigit() and len(raw) == 4:
            mm = int(raw[:2])
            ss = int(raw[2:])
            if ss >= 60:
                print("⚠️ Seconds must be < 60.")
                continue
            return mm * 60 + ss
        print("⚠️ Time must be 4 digits in MMSS format (e.g., 0930).")


def get_optional_valid_time(prompt: str) -> Optional[int]:
    raw = input(prompt).strip()
    if not raw:
        return None
    if raw.isdigit() and len(raw) == 4:
        mm = int(raw[:2])
        ss = int(raw[2:])
        if ss >= 60:
            print("⚠️ Seconds must be < 60.")
            return None
        return mm * 60 + ss
    print("⚠️ Time must be 4 digits in MMSS format (e.g., 0930).")
    return None

def get_optional_choice(prompt: str, choices: Dict[str, str]) -> Optional[str]:
    while True:
        print(prompt)
        for k, v in choices.items():
            print(f"{k}. {v}")
        choice = input("Choose (1–5, or Enter to skip): ").strip()
        if not choice:
            return None
        if choice in choices:
            return choices[choice].lower()
        print(f"⚠️ Invalid choice '{choice}'. Please enter one of {list(choices.keys())}.")

# --- Core validated input ---
def _validated_input_core(
    prompt: str,
    cast_func: Callable[[str], Any],
    min_val: Optional[float],
    max_val: Optional[float],
    allow_blank: bool
) -> Optional[Any]:
    while True:
        raw = input(prompt).strip()

        # Blank handling
        if allow_blank and not raw:
            return None
        if not allow_blank and not raw:
            print("⚠️ This field is required. Please enter a value.")
            continue

        try:
            value = cast_func(raw)
            if isinstance(value, str):
                value = value.lower()
            if isinstance(value, (int, float)):
                if (min_val is not None and value < min_val) or (max_val is not None and value > max_val):
                    if min_val is not None and max_val is not None:
                        print(f"⚠️ Value must be between {min_val} and {max_val}. Try again.")
                    elif min_val is not None:
                        print(f"⚠️ Value must be ≥ {min_val}. Try again.")
                    elif max_val is not None:
                        print(f"⚠️ Value must be ≤ {max_val}. Try again.")
                    continue
            return value
        except ValueError:
            expected = cast_func.__name__
            print(f"⚠️ Invalid input. Expecting {expected} value.")

def get_validated_input(
    prompt: str,
    cast_func: Callable[[str], Any],
    min_val: Optional[float] = None,
    max_val: Optional[float] = None
) -> Any:
    return _validated_input_core(prompt, cast_func, min_val, max_val, allow_blank=False)

def get_optional_validated_input(
    prompt: str,
    cast_func: Callable[[str], Any],
    min_val: Optional[float] = None,
    max_val: Optional[float] = None
) -> Optional[Any]:
    return _validated_input_core(prompt, cast_func, min_val, max_val, allow_blank=True)
