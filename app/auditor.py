import math
from collections import defaultdict
from datetime import datetime
from typing import Iterable, List, Dict
from app.utils import normalize_text, normalize_amount, parse_float

# ----------------------------
# Feature 1: Find duplicate 
# ----------------------------
def find_duplicate_invoices(rows: Iterable[Dict[str, str]],
                            merchant_col: str = "merchant",
                            invoice_col: str = "invoice_no",
                            amount_col: str = "amount_usd",
                            include_merchant: bool = True) -> List[Dict[str, str]]:
    """
    Return all groups of duplicate invoices (count >= 2).
    """
    buckets = defaultdict(list)

    for r in rows:
        inv = normalize_text(r.get(invoice_col))
        amt = normalize_amount(r.get(amount_col))
        if include_merchant:
            m = normalize_text(r.get(merchant_col))
            key = (m, inv, amt)
        else:
            key = (inv, amt)
        buckets[key].append(r)

    dups: List[Dict[str, str]] = []
    for _, group in buckets.items():
        if len(group) >= 2:
            for item in group:
                rec = dict(item)
                rec["_reason"] = "duplicate"
                rec["_dup_count"] = len(group)
                dups.append(rec)

    dups.sort(key=lambda x: (
        normalize_text(x.get(merchant_col)) if include_merchant else "",
        normalize_text(x.get(invoice_col)),
        normalize_amount(x.get(amount_col)),
    ))
    return dups

# ----------------------------
# Feature 2: Flag weekends
# ----------------------------
def flag_weekends(rows: Iterable[Dict[str, str]],
                  date_col: str = "expense_date",
                  date_fmts: tuple[str, ...] = ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d")) -> List[Dict[str, str]]:
    """Flag weekend transactions; tolerant to a few common date formats."""
    flagged: List[Dict[str, str]] = []
    for r in rows:
        s = (r.get(date_col) or "").strip()
        if not s:
            continue
        dt = None
        for fmt in date_fmts:
            try:
                dt = datetime.strptime(s, fmt)
                break
            except ValueError:
                continue
        if not dt:
            continue
        if dt.weekday() >= 5:
            copy = dict(r)
            copy["_reason"] = "weekend"
            flagged.append(copy)
    return flagged

# ----------------------------
# Feature 3: Flag threshold
# ----------------------------
def flag_threshold(rows: Iterable[Dict[str, str]],
                   amount_col: str = "amount_usd",
                   limit: float = 5000.0,
                   buffer: float = 200.0) -> List[Dict[str, str]]:
    """Flag threshold violations."""
    flagged: List[Dict[str, str]] = []
    for r in rows:
        amt = parse_float(r.get(amount_col))
        if amt is None:
            continue
        reason = None
        if amt > limit:
            reason = "over_limit"
        elif (limit - buffer) < amt <= limit:
            reason = "near_limit"
        if reason:
            copy = dict(r)
            copy["_reason"] = reason
            flagged.append(copy)
    return flagged

# ----------------------------
# Feature 4: Benford's Law Analysis
# ----------------------------
def calculate_benford_stats(rows: Iterable[Dict[str, str]], amount_col: str = "amount_usd") -> Dict:
    """
    Calculate the distribution of leading digits (1-9) in expense amounts.
    """
    actual_counts = {d: 0 for d in range(1, 10)}
    total_valid = 0
    
    benford_probs = {d: math.log10(1 + 1/d) for d in range(1, 10)}
    
    for r in rows:
        amt_str = r.get(amount_col, "")
        digits = [c for c in amt_str if c.isdigit() and c != '0']
        if digits:
            first_digit = int(digits[0])
            actual_counts[first_digit] += 1
            total_valid += 1
            
    if total_valid == 0:
        return {"error": "No valid amounts found"}

    stats = []
    max_deviation = 0
    
    for d in range(1, 10):
        actual_freq = actual_counts[d] / total_valid
        expected_freq = benford_probs[d]
        diff = abs(actual_freq - expected_freq)
        max_deviation = max(max_deviation, diff)
        
        stats.append({
            "digit": d,
            "actual_count": actual_counts[d],
            "actual_pct": round(actual_freq * 100, 2),
            "expected_pct": round(expected_freq * 100, 2),
            "diff_pct": round(diff * 100, 2)
        })
        
    return {
        "total_analyzed": total_valid,
        "stats": stats,
        "is_suspicious": max_deviation > 0.05,
        "max_deviation_pct": round(max_deviation * 100, 2)
    }

# ----------------------------
# Feature 5: Suspicious Keywords
# ----------------------------
SUSPICIOUS_TERMS = [
    "cash", "gift", "party", "casino", "spa", "personal", 
    "misc", "various", "round", "facilitation", "consulting"
]

def flag_suspicious_keywords(rows: Iterable[Dict[str, str]], 
                           check_cols: List[str] = ["merchant", "category", "employee"]) -> List[Dict[str, str]]:
    """Flag rows containing suspicious keywords in specified columns."""
    flagged: List[Dict[str, str]] = []
    
    for r in rows:
        found_terms = []
        for col in check_cols:
            val = normalize_text(r.get(col, ""))
            for term in SUSPICIOUS_TERMS:
                if term in val:
                    found_terms.append(f"{term} (in {col})")
        
        if found_terms:
            copy = dict(r)
            copy["_reason"] = "suspicious_keyword"
            copy["_details"] = ", ".join(found_terms)
            flagged.append(copy)
            
    return flagged

# ----------------------------
# Feature 6: Payment Discrepancies
# ----------------------------
def flag_discrepancies(rows: Iterable[Dict[str, str]], 
                      incurred_col: str = "amount_usd",
                      paid_col: str = "paid_amount_usd") -> List[Dict[str, str]]:
    """Flag rows where incurred amount != paid amount."""
    flagged: List[Dict[str, str]] = []
    
    for r in rows:
        incurred = parse_float(r.get(incurred_col))
        paid = parse_float(r.get(paid_col))
        
        if incurred is None or paid is None:
            continue
            
        diff = abs(incurred - paid)
        if diff > 0.01:
            copy = dict(r)
            copy["_reason"] = "discrepancy"
            copy["_details"] = f"Diff: ${diff:.2f}"
            flagged.append(copy)
            
    return flagged

