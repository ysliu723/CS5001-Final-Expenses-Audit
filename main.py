from typing import List, Optional
import os
import sys
import argparse
from app import state
from app.utils import load_rows
from app.web import app
from app.cli import run_menu
from app.auditor import (
    find_duplicate_invoices, flag_weekends, flag_threshold,
    flag_suspicious_keywords, calculate_benford_stats, flag_discrepancies
)

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("csv")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("menu")
    sub.add_parser("web")
    
    # Query commands
    pd = sub.add_parser("find-duplicates")
    pd.add_argument("--limit", type=int, default=20)
    
    pw = sub.add_parser("flag-weekends")
    pw.add_argument("--limit", type=int, default=20)
    
    pt = sub.add_parser("flag-threshold")
    pt.add_argument("--limit", type=float, default=5000.0)
    pt.add_argument("--buffer", type=float, default=200.0)
    pt.add_argument("--limit-print", type=int, default=20)
    
    # New feature commands
    sub.add_parser("benford-analysis")
    sub.add_parser("suspicious-keywords")
    sub.add_parser("payment-discrepancies")
    
    return p

def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    
    if not os.path.exists(args.csv):
        print(f" Not found: {args.csv}")
        return 1
    
    # Initialize global state
    state.CSV_PATH = args.csv
    state.ROWS = load_rows(state.CSV_PATH)
    
    if not state.ROWS:
       print(" No data loaded from the CSV file.")
       return 1

    if args.cmd == "web":
        print("\n Starting Expenses Audit Web Server...")
        print(" Open your browser and go to: http://127.0.0.1:5001")
        print("  Press Ctrl+C to stop the server\n")
        # Disable debug mode for cleaner output, use port 5001 to avoid conflicts
        app.run(debug=False, port=5001)
        return 0
    
    if args.cmd == "menu":
        run_menu()
        return 0

    # CLI Commands
    if args.cmd == "find-duplicates":
        res = find_duplicate_invoices(state.ROWS)
        print(f"Found {len(res)} duplicates (showing first {args.limit}):")
        for r in res[:args.limit]:
            print(f"{r.get('merchant')} | {r.get('invoice_no')} | ${r.get('amount_usd')}")
        return 0

    if args.cmd == "flag-weekends":
        res = flag_weekends(state.ROWS)
        print(f"Found {len(res)} weekend transactions (showing first {args.limit}):")
        for r in res[:args.limit]:
            print(f"{r.get('expense_date')} | {r.get('merchant')} | ${r.get('amount_usd')}")
        return 0

    if args.cmd == "flag-threshold":
        res = flag_threshold(state.ROWS, limit=args.limit, buffer=args.buffer)
        print(f"Found {len(res)} threshold violations (showing first {args.limit_print}):")
        for r in res[:args.limit_print]:
            print(f"{r.get('expense_date')} | {r.get('merchant')} | ${r.get('amount_usd')} ({r.get('_reason')})")
        return 0
        
    if args.cmd == "benford-analysis":
        res = calculate_benford_stats(state.ROWS)
        if res.get("error"):
            print(f"Error: {res.get('error')}")
        else:
            print(f"Benford Analysis (Analyzed {res['total_analyzed']} records)")
            print(f"Suspicious: {res['is_suspicious']} (Max deviation: {res['max_deviation_pct']}%)")
        return 0
        
    if args.cmd == "suspicious-keywords":
        res = flag_suspicious_keywords(state.ROWS)
        print(f"Found {len(res)} records with suspicious keywords:")
        for r in res[:20]:
            print(f"{r.get('merchant')} | {r.get('category')} | {r.get('_details')}")
        return 0
        
    if args.cmd == "payment-discrepancies":
        res = flag_discrepancies(state.ROWS)
        print(f"Found {len(res)} payment discrepancies:")
        for r in res[:20]:
            print(f"{r.get('invoice_no')} | Amount: {r.get('amount_usd')} | Paid: {r.get('paid_amount_usd')} | {r.get('_details')}")
        return 0

    return 0

if __name__ == "__main__":
    raise SystemExit(main())

