from datetime import datetime
from typing import Callable, Optional, Dict, Any
from .schemas import RoastSession, SensoryScores
from .storage import save_session

# --- Object Creators ---
def create_roast_session(**kwargs) -> RoastSession:
    return RoastSession(**kwargs)

def create_sensory(**kwargs) -> SensoryScores:
    return SensoryScores(**kwargs)

def log_roast(session_kwargs, controls_data, sensory_kwargs):
    session = create_roast_session(**session_kwargs)
    sensory = create_sensory(**sensory_kwargs)
    save_session(session, sensory)

# --- Input Utilities ---
def parse_date_flexible(date_str: str) -> datetime:
    """Try multiple common date formats and force 2-digit years into 2000s."""
    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            dt = datetime.strptime(date_str, fmt)
            if dt.year < 2000:
                dt = dt.replace(year=dt.year + 2000 if dt.year < 100 else dt.year)
            return dt
        except ValueError:
            continue
    raise ValueError(
        f"Unrecognized date format: {date_str}. Try MM/DD/YYYY, MM/DD/YY, or YYYY-MM-DD."
    )

def get_validated_date(prompt: str, allow_blank: bool = False) -> Optional[datetime]:
    """Prompt until a valid date (or blank if allowed) is entered."""
    while True:
        s = input(prompt).strip()
        if not s and allow_blank:
            return None
        try:
            return parse_date_flexible(s)
        except ValueError as e:
            print(f"⚠️ {e}")

def mmss_to_seconds(mmss: str) -> int:
    """Convert 'MMSS' into total seconds. Raises ValueError if invalid."""
    s = mmss.strip()
    if not s.isdigit() or len(s) != 4:
        raise ValueError("Time must be 4 digits in MMSS format (e.g., 0930).")
    val = int(s)
    mm = val // 100
    ss = val % 100
    if ss >= 60:
        raise ValueError("Seconds must be < 60 (e.g., 0959 is max).")
    return mm * 60 + ss

def seconds_to_mmss(seconds):
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
    """Prompt until a valid MMSS is entered; returns seconds as int."""
    while True:
        raw = input(prompt).strip()
        try:
            return mmss_to_seconds(raw)
        except ValueError as e:
            print(f"⚠️ {e}")

def get_optional_valid_time(prompt: str) -> Optional[int]:
    """Prompt for MMSS; empty returns None; else returns seconds as int."""
    while True:
        raw = input(prompt).strip()
        if raw == "":
            return None
        try:
            return mmss_to_seconds(raw)
        except ValueError as e:
            print(f"⚠️ {e}")

def get_optional_choice(prompt: str, choices: Dict[str, str]) -> Optional[str]:
    """Prompt until a valid choice key is entered, or blank returns None."""
    while True:
        print(prompt)
        for k, v in choices.items():
            print(f"{k}. {v}")
        choice = input("Choose (1–5, or Enter to skip): ").strip()
        if not choice:
            return None
        if choice in choices:
            return choices[choice].lower()
        print("⚠️ Invalid choice. Try again.")

# --- Core validated input ---
def _validated_input_core(
    prompt: str,
    cast_func: Callable[[str], Any],
    min_val: Optional[float],
    max_val: Optional[float],
    allow_blank: bool
) -> Optional[Any]:
    if min_val is not None and max_val is not None:
        prompt = f"{prompt} [{min_val}–{max_val}]: "
    elif min_val is not None:
        prompt = f"{prompt} [≥ {min_val}]: "
    elif max_val is not None:
        prompt = f"{prompt} [≤ {max_val}]: "

    while True:
        raw = input(prompt).strip()

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
                    print(f"⚠️ Value must be between {min_val} and {max_val}. Try again.")
                    continue
            return value
        except ValueError:
            print("⚠️ Invalid input format. Try again.")

def get_validated_input(
    prompt: str,
    cast_func: Callable[[str], Any],
    min_val: Optional[float] = None,
    max_val: Optional[float] = None
) -> Any:
    """Required input — will never return None."""
    return _validated_input_core(prompt, cast_func, min_val, max_val, allow_blank=False)

def get_optional_validated_input(
    prompt: str,
    cast_func: Callable[[str], Any],
    min_val: Optional[float] = None,
    max_val: Optional[float] = None
) -> Optional[Any]:
    """Optional input — pressing Enter returns None."""
    return _validated_input_core(prompt, cast_func, min_val, max_val, allow_blank=True)
