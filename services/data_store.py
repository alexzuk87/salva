"""Capa de persistencia CSV para SALVA."""

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

PROFESSIONALS_FILE = DATA_DIR / "professionals.csv"
BOOKINGS_FILE = DATA_DIR / "bookings.csv"
RATINGS_FILE = DATA_DIR / "ratings.csv"
REVIEWS_FILE = DATA_DIR / "reviews.csv"
NEIGHBORHOOD_JOBS_FILE = DATA_DIR / "neighborhood_jobs.csv"
COMPLAINTS_FILE = DATA_DIR / "complaints.csv"
HOME_HISTORY_FILE = DATA_DIR / "home_history.csv"
HOME_PROFILES_FILE = DATA_DIR / "home_profiles.csv"
SAVINGS_GOALS_FILE = DATA_DIR / "savings_goals.csv"
PLANNER_TASKS_FILE = DATA_DIR / "planner_tasks.csv"
CHAT_MESSAGES_FILE = DATA_DIR / "chat_messages.csv"
ACCOUNTS_FILE = DATA_DIR / "accounts.csv"
ACCOUNT_TRANSACTIONS_FILE = DATA_DIR / "account_transactions.csv"


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path, columns: list[str]) -> pd.DataFrame:
    ensure_data_dir()
    if not path.exists():
        return pd.DataFrame({col: pd.Series(dtype="object") for col in columns})
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    for col in columns:
        if col not in df.columns:
            df[col] = ""
    return df[columns]


def write_csv(path: Path, df: pd.DataFrame) -> None:
    ensure_data_dir()
    df.to_csv(path, index=False)


def next_id(df: pd.DataFrame, prefix: str) -> str:
    if df.empty or "id" not in df.columns:
        return f"{prefix}001"
    numeric = df["id"].str.replace(prefix, "", regex=False).astype(int)
    return f"{prefix}{numeric.max() + 1:03d}"


def ensure_all_csv_files() -> None:
    """Crea CSV faltantes o vacíos con encabezados válidos (despliegue Linux/Cloud)."""
    from services.bookings import BOOKING_COLUMNS
    from services.complaints import COMPLAINT_COLUMNS
    from services.goals import GOAL_COLUMNS
    from services.home_history import HISTORY_COLUMNS
    from services.neighborhoods import NEIGHBORHOOD_JOB_COLUMNS
    from services.planner import TASK_COLUMNS
    from services.predict import PROFILE_COLUMNS
    from services.professionals import PROFESSIONAL_COLUMNS, seed_professionals
    from services.ratings import RATING_COLUMNS
    from services.chat import CHAT_COLUMNS
    from services.accounts import ACCOUNT_COLUMNS, TRANSACTION_COLUMNS, seed_accounts
    from services.reviews import REVIEW_COLUMNS, seed_reviews

    schemas = [
        (PROFESSIONALS_FILE, PROFESSIONAL_COLUMNS),
        (BOOKINGS_FILE, BOOKING_COLUMNS),
        (RATINGS_FILE, RATING_COLUMNS),
        (REVIEWS_FILE, REVIEW_COLUMNS),
        (NEIGHBORHOOD_JOBS_FILE, NEIGHBORHOOD_JOB_COLUMNS),
        (COMPLAINTS_FILE, COMPLAINT_COLUMNS),
        (HOME_HISTORY_FILE, HISTORY_COLUMNS),
        (HOME_PROFILES_FILE, PROFILE_COLUMNS),
        (SAVINGS_GOALS_FILE, GOAL_COLUMNS),
        (PLANNER_TASKS_FILE, TASK_COLUMNS),
        (CHAT_MESSAGES_FILE, CHAT_COLUMNS),
        (ACCOUNTS_FILE, ACCOUNT_COLUMNS),
        (ACCOUNT_TRANSACTIONS_FILE, TRANSACTION_COLUMNS),
    ]
    ensure_data_dir()
    for path, columns in schemas:
        if not path.is_file() or path.stat().st_size == 0:
            write_csv(path, pd.DataFrame(columns=columns))

    seed_professionals()
    seed_reviews()
    seed_accounts()
    _ensure_pro_photos()
    from services.neighborhoods import seed_neighborhood_jobs

    seed_neighborhood_jobs()


def _ensure_pro_photos() -> None:
    from services.pro_photos import PHOTO_DIR, audit_professional_photos
    from services.professionals import load_professionals

    if not PHOTO_DIR.is_dir() or audit_professional_photos(load_professionals()):
        import sys
        from pathlib import Path

        root = Path(__file__).resolve().parent.parent
        sys.path.insert(0, str(root))
        try:
            from scripts.gen_local_avatars import generate_local_avatars
            generate_local_avatars()
        except Exception:
            pass
