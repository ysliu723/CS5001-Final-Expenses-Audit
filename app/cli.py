from datetime import datetime
from app import state
from app.utils import parse_float, save_rows
from app.auditor import (
    find_duplicate_invoices, flag_weekends, flag_threshold
)
from app.web import app

def show_welcome():
    print("=" * 60)
    print("   Welcome to Expenses Audit Tool")
    print("This tool helps you audit expense data efficiently.")
    print("=" * 60)

def show_menu():
    print("\n================= Expenses Audit Tool Menu =================")
    print(" Query Operations:")
    print("  1. Find duplicate invoices")
    print("  2. Flag weekend transactions")
    print("  3. Flag threshold violations")
    print("\n Data Management:")
    print("  4. Add new expense record")
    print("  5. Update existing record")
    print("  6. Delete record")
    print("\n Other:")
    print("  7. Open Web Interface")
    print("  8. Quit")
    print("============================================================")

def run_menu() -> None:
    """Interactive CLI menu."""
    show_welcome()

    while True:
        show_menu()
        choice = input("Enter your choice (1-8): ").strip()

        if choice == "1":
            dups = find_duplicate_invoices(state.ROWS)
            print(f"\nFound {len(dups)} duplicate invoices (showing first 20):")
            for r in dups[:20]:
                print(f"{r.get('merchant')} | {r.get('invoice_no')} | ${r.get('amount_usd')}")
            state.LAST_RESULTS = dups

        elif choice == "2":
            res = flag_weekends(state.ROWS)
            print(f"\nFound {len(res)} weekend transactions (showing first 20):")
            for r in res[:20]:
                print(f"{r.get('expense_date')} | {r.get('merchant')} | ${r.get('amount_usd')}")
            state.LAST_RESULTS = res

        elif choice == "3":
            try:
                limit = float(input("Enter limit (default 5000): ").strip() or "5000")
                buffer = float(input("Enter buffer (default 200): ").strip() or "200")
            except ValueError:
                print("Invalid number, using defaults 5000 / 200")
                limit, buffer = 5000.0, 200.0
            res = flag_threshold(state.ROWS, limit=limit, buffer=buffer)
            print(f"\nFound {len(res)} threshold violations (showing first 20):")
            for r in res[:20]:
                print(f"{r.get('expense_date')} | {r.get('merchant')} | ${r.get('amount_usd')} ({r.get('_reason')})")
            state.LAST_RESULTS = res

        elif choice == "4":
            # Add new record
            print("\n Add New Expense Record")
            print("=" * 60)
            try:
                new_record = {}
                new_record['expense_id'] = input("Expense ID *: ").strip()
                if not new_record['expense_id']:
                    print(" Expense ID is required!")
                    continue
                
                if any(r.get('expense_id') == new_record['expense_id'] for r in state.ROWS):
                    print(f" Expense ID '{new_record['expense_id']}' already exists!")
                    continue
                
                new_record['employee'] = input("Employee *: ").strip()
                new_record['department'] = input("Department *: ").strip()
                new_record['expense_date'] = input("Expense Date (YYYY-MM-DD) *: ").strip()
                
                try:
                    datetime.strptime(new_record['expense_date'], '%Y-%m-%d')
                except ValueError:
                    print(" Invalid date format! Use YYYY-MM-DD")
                    continue
                
                new_record['amount_usd'] = input("Amount USD *: ").strip()
                if parse_float(new_record['amount_usd']) is None:
                    print(" Invalid amount!")
                    continue
                
                new_record['currency'] = input("Currency (default USD): ").strip() or "USD"
                new_record['category'] = input("Category (Meal/Hotel/Air/Client Gift/Other) *: ").strip()
                new_record['merchant'] = input("Merchant *: ").strip()
                new_record['invoice_no'] = input("Invoice No *: ").strip()
                new_record['invoice_city'] = input("Invoice City: ").strip()
                new_record['trip_to_city'] = input("Trip To City: ").strip()
                new_record['approver'] = input("Approver: ").strip()
                new_record['paid_amount_usd'] = input("Paid Amount USD: ").strip() or new_record['amount_usd']
                
                state.ROWS.append(new_record)
                
                if save_rows(state.CSV_PATH, state.ROWS):
                    print(" Record added successfully!")
                else:
                    state.ROWS.pop()
                    print(" Failed to save to CSV!")
            except Exception as e:
                print(f" Error adding record: {e}")

        elif choice == "5":
            # Update record
            print("\n Update Expense Record")
            print("=" * 60)
            expense_id = input("Enter Expense ID to update: ").strip()
            
            record_index = None
            for i, r in enumerate(state.ROWS):
                if r.get('expense_id') == expense_id:
                    record_index = i
                    break
            
            if record_index is None:
                print(f" Record with ID '{expense_id}' not found!")
                continue
            
            print("\nCurrent record:")
            for k, v in state.ROWS[record_index].items():
                print(f"  {k}: {v}")
            
            print("\nEnter new values (press Enter to keep current value):")
            old_record = dict(state.ROWS[record_index])
            
            try:
                for field in ['employee', 'department', 'expense_date', 'amount_usd', 
                             'currency', 'category', 'merchant', 'invoice_no', 
                             'invoice_city', 'trip_to_city', 'approver', 'paid_amount_usd']:
                    new_value = input(f"{field} [{old_record.get(field, '')}]: ").strip()
                    if new_value:
                        if field == 'expense_date':
                            try:
                                datetime.strptime(new_value, '%Y-%m-%d')
                            except ValueError:
                                print(" Invalid date format! Keeping old value.")
                                continue
                        if field in ['amount_usd', 'paid_amount_usd'] and parse_float(new_value) is None:
                            print(" Invalid amount! Keeping old value.")
                            continue
                        state.ROWS[record_index][field] = new_value
                
                if save_rows(state.CSV_PATH, state.ROWS):
                    print(" Record updated successfully!")
                else:
                    state.ROWS[record_index] = old_record
                    print(" Failed to save to CSV!")
            except Exception as e:
                state.ROWS[record_index] = old_record
                print(f" Error updating record: {e}")

        elif choice == "6":
            # Delete record
            print("\n Delete Expense Record")
            print("=" * 60)
            expense_id = input("Enter Expense ID to delete: ").strip()
            
            record_index = None
            for i, r in enumerate(state.ROWS):
                if r.get('expense_id') == expense_id:
                    record_index = i
                    break
            
            if record_index is None:
                print(f" Record with ID '{expense_id}' not found!")
                continue
            
            print("\nRecord to delete:")
            for k, v in state.ROWS[record_index].items():
                print(f"  {k}: {v}")
            
            confirm = input("\n Are you sure you want to delete this record? (yes/no): ").strip().lower()
            if confirm != 'yes':
                print(" Deletion cancelled.")
                continue
            
            deleted_record = state.ROWS.pop(record_index)
            
            if save_rows(state.CSV_PATH, state.ROWS):
                print(" Record deleted successfully!")
            else:
                state.ROWS.insert(record_index, deleted_record)
                print(" Failed to save to CSV!")

        elif choice == "7":
            print("\n Starting web server...")
            print(" Open your browser and go to: http://127.0.0.1:5001")
            print("  Press Ctrl+C to stop the server\n")
            app.run(debug=True, use_reloader=False)

        elif choice == "8":
            print("\nThank you for using the Expenses Audit Tool. Goodbye!")
            break

        else:
            print("  Invalid input. Please enter a number between 1 and 8.")

