from pathlib import Path
from uuid import uuid4

from app.core.config import get_settings

settings = get_settings()


def save_bytes(content: bytes, original_name: str) -> str:
    storage_dir = Path(settings.storage_path)
    storage_dir.mkdir(parents=True, exist_ok=True)
    ext = Path(original_name).suffix
    filename = f"{uuid4().hex}{ext}"
    full_path = storage_dir / filename
    full_path.write_bytes(content)
    return str(full_path)
