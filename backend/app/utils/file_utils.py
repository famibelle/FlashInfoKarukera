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
    
    # Format 1: horoscope-YYYYMMDD-edition.txt (existing files)
    date_str_no_dash = date.strftime("%Y%m%d")
    filename1 = f"horoscope-{date_str_no_dash}-{edition}.txt"
    filepath1 = archives_dir / filename1
    if filepath1.exists():
        return filepath1
    
    # Format 2: YYYY-MM-DD-edition.txt
    filename2 = f"{date.isoformat()}-{edition}.txt"
    filepath2 = archives_dir / filename2
    if filepath2.exists():
        return filepath2
    
    # Try other formats
    for ext in ["txt", "md", ""]:
        for fmt in [f"{date.year}/{date.month:02d}/{date.day:02d}-{edition}", 
                     f"{date.isoformat()}-{edition}",
                     f"{edition}-{date.isoformat()}",
                     f"horoscope-{date_str_no_dash}-{edition}"]:
            test_path = archives_dir / f"{fmt}.{ext}" if ext else archives_dir / fmt
            if test_path.exists():
                return test_path
    
    return None


def extract_sign_sections(content: str) -> Dict[str, str]:
    """Extract sign sections from horoscope content."""
    from .zodiac_utils import ZODIAC_SIGNS
    
    sections = {}
    current_sign = None
    
    # Get list of valid sign names (French and English)
    valid_sign_names = set()
    for sign in ZODIAC_SIGNS:
        valid_sign_names.add(sign["name_fr"].upper())
        valid_sign_names.add(sign["name_en"].upper())
    
    for line in content.split("\n"):
        line = line.strip()
        if not line:
            continue
        
        # Check if line is a sign header (=== SIGNE === or ## SIGNE)
        if line.startswith("===") or line.startswith("###") or line.startswith("##"):
            # Extract sign name
            sign_name = line.replace("=", "").replace("#", "").strip().upper()
            if sign_name and sign_name in valid_sign_names:
                current_sign = sign_name
                sections[current_sign] = ""
            else:
                current_sign = None
        elif current_sign:
            sections[current_sign] += line + "\n"
    
    # Convert keys back to proper case (French names)
    result = {}
    for key, value in sections.items():
        # Find the proper French name
        for sign in ZODIAC_SIGNS:
            if sign["name_fr"].upper() == key or sign["name_en"].upper() == key:
                result[sign["name_fr"]] = value.strip()
                break
    
    return result


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
