"""File utilities for horoscope."""
from pathlib import Path
from app.config import settings
from typing import Dict, Optional, List


def read_file(filepath: Path) -> str:
    """Read file content."""
    return filepath.read_text(encoding="utf-8")


def find_horoscope_file(date, edition: str) -> Optional[Path]:
    """Find horoscope file for given date and edition."""
    archives_dir = settings.ARCHIVES_DIR
    if not archives_dir.exists():
        return None
    
    # Try format: YYYY-MM-DD-edition.txt
    filename = f"{date.isoformat()}-{edition}.txt"
    filepath = archives_dir / filename
    if filepath.exists():
        return filepath
    
    # Try other formats
    for ext in ["txt", "md", ""]:
        for fmt in [f"{date.year}/{date.month:02d}/{date.day:02d}-{edition}", 
                     f"{date.isoformat()}-{edition}",
                     f"{edition}-{date.isoformat()}"]:
            test_path = archives_dir / f"{fmt}.{ext}" if ext else archives_dir / fmt
            if test_path.exists():
                return test_path
    
    return None


def extract_sign_sections(content: str) -> Dict[str, str]:
    """Extract sign sections from horoscope content."""
    sections = {}
    current_sign = None
    
    for line in content.split("\n"):
        line = line.strip()
        if not line:
            continue
        
        # Check if line is a sign header (=== SIGNE === or ## SIGNE)
        if line.startswith("===") or line.startswith("###") or line.startswith("##"):
            # Extract sign name
            sign_name = line.replace("=", "").replace("#", "").strip()
            if sign_name:
                current_sign = sign_name
                sections[current_sign] = ""
        elif current_sign:
            sections[current_sign] += line + "\n"
    
    return sections


def list_horoscope_archives() -> List[Dict]:
    """List all available horoscope archives."""
    archives_dir = settings.ARCHIVES_DIR
    if not archives_dir.exists():
        return []
    
    archives = []
    for filepath in archives_dir.rglob("*.txt"):
        try:
            # Parse filename: YYYY-MM-DD-edition.txt
            name = filepath.stem
            parts = name.split("-")
            if len(parts) >= 3:
                date_str = "-".join(parts[:3])
                edition = parts[3] if len(parts) > 3 else "unknown"
                archives.append({
                    "date": date_str,
                    "edition": edition,
                    "file": str(filepath.relative_to(settings.PROJECT_ROOT))
                })
        except Exception:
            continue
    
    return archives
