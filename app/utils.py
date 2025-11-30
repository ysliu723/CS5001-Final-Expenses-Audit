import csv
import unicodedata
from typing import List, Dict, Any, Optional, Union

def load_rows(csv_path: str, encoding: str = "utf-8") -> List[Dict[str, str]]:  
    """
    This function reads a CSV file and gives back a list of rows.
    Each row is a small dictionary like {'merchant': 'Acme', 'amount_usd': '100'}.
    It tries multiple encodings to read the file.
    """
    # Try a few different text encodings.
    for enc in (encoding, "utf-8-sig", "cp1252"):
        try:
            with open(csv_path, "r", encoding=enc, newline="") as f:
                return list(csv.DictReader(f))
        except UnicodeDecodeError:
            continue
    # If all encodings fail, try one last time and let Python show the error
    with open(csv_path, "r", encoding=encoding, newline="") as f:
        return list(csv.DictReader(f))

def save_rows(csv_path: str, rows: List[Dict[str, str]], encoding: str = "utf-8-sig") -> bool:
    """
    Save rows back to CSV file with proper error handling.
    Returns True if successful, False otherwise.
    """
    try:
        if not rows:
            print(" Warning: Attempting to save empty dataset")
            return False
        
        # Get all unique fieldnames from all rows
        fieldnames = []
        seen = set()
        for row in rows:
            for key in row.keys():
                if key not in seen:
                    fieldnames.append(key)
                    seen.add(key)
        
        # Write to temporary file first for safety
        temp_path = csv_path + ".tmp"
        with open(temp_path, "w", encoding=encoding, newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        # Replace original file with temp file
        import shutil
        import os
        shutil.move(temp_path, csv_path)
        return True
    except Exception as e:
        print(f" Error saving CSV: {e}")
        return False

def parse_float(s: Optional[str]) -> Optional[float]:
    """
    This function changes a money string like '$1,200.50' into a number 1200.50.
    If it cannot do that, it returns None.
    """
    if not s:
        return None
    try:
        raw = str(s).replace("$", "").replace(",", "").strip()
        return float(raw)
    except ValueError:
        return None

# Normalization helpers
_DASH_MAP = dict.fromkeys(map(ord, "‐-‒–—―﹘﹣－"), ord("-"))  # unify various dashes to '-'

def normalize_text(s: Optional[str]) -> str:
    """unify text: Unicode NFKC, unify dashes to '-', strip, lower.""" 
    if s is None:
        return ""
    s = str(s)
    s = unicodedata.normalize("NFKC", s)
    s = s.translate(_DASH_MAP)
    s = s.strip().lower()
    return s

def normalize_amount(s: Optional[str]) -> str:
    """unify amount: remove $, commas, strip, float format to 2 decimals."""
    if s is None:
        return ""
    raw = str(s).replace("$", "").replace(",", "").strip()
    try:
        return f"{float(raw):.2f}"
    except ValueError:
        return ""

