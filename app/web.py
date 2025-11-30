import io
import csv
from datetime import datetime
from flask import Flask, render_template, request, send_file, jsonify
from app import state
from app.utils import parse_float, save_rows
from app.auditor import (
    find_duplicate_invoices, flag_weekends, flag_threshold,
    calculate_benford_stats, flag_suspicious_keywords, flag_discrepancies
)

app = Flask(__name__, template_folder="../templates")

@app.route('/')
def index():
    """Main page."""
    # Calculate dataset summary stats
    total_amount = 0.0
    dates = []
    
    for r in state.ROWS:
        amt = parse_float(r.get('amount_usd'))
        if amt is not None:
            total_amount += amt
            
        d_str = r.get('expense_date')
        if d_str:
            try:
                # Try common formats
                dt = None
                for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"):
                    try:
                        dt = datetime.strptime(d_str, fmt)
                        break
                    except ValueError:
                        continue
                if dt:
                    dates.append(dt)
            except:
                pass
    
    date_range = "N/A"
    if dates:
        min_date = min(dates).strftime("%Y-%m-%d")
        max_date = max(dates).strftime("%Y-%m-%d")
        date_range = f"{min_date} to {max_date}"
        
    fmt_amount = f"${total_amount:,.2f}"

    return render_template("index.html",
                         total_rows=len(state.ROWS),
                         total_amount=fmt_amount,
                         date_range=date_range)

@app.route('/api/all')
def api_all():
    """Return all rows with pagination support."""
    offset = int(request.args.get('offset', 0))
    limit = int(request.args.get('limit', 100))
    
    # Slice the data
    data = state.ROWS[offset : offset + limit]
    
    # Update last results only if it's a fresh search (offset 0)
    # or we could decide to accumulate. For simplicity, let's just return data.
    # NOTE: "Download" usually downloads *everything* or *current view*.
    # To keep download consistent, we might want to set LAST_RESULTS = ROWS
    if offset == 0:
        state.LAST_RESULTS = state.ROWS
        
    return jsonify({
        "data": data,
        "total": len(state.ROWS),
        "has_more": (offset + limit) < len(state.ROWS)
    })

@app.route('/api/duplicates')
def api_duplicates():
    """Return duplicates."""
    state.LAST_RESULTS = find_duplicate_invoices(state.ROWS)
    return jsonify(state.LAST_RESULTS)

@app.route('/api/weekends')
def api_weekends():
    """Return weekend transactions."""
    state.LAST_RESULTS = flag_weekends(state.ROWS)
    return jsonify(state.LAST_RESULTS)

@app.route('/api/threshold')
def api_threshold():
    """Return threshold violations."""
    limit = parse_float(request.args.get('limit')) or 5000.0
    buffer = parse_float(request.args.get('buffer')) or 200.0
    state.LAST_RESULTS = flag_threshold(state.ROWS, limit=limit, buffer=buffer)
    return jsonify(state.LAST_RESULTS)

@app.route('/api/benford')
def api_benford():
    """Return Benford's Law analysis stats."""
    return jsonify(calculate_benford_stats(state.ROWS))

@app.route('/api/suspicious')
def api_suspicious():
    """Return rows with suspicious keywords."""
    state.LAST_RESULTS = flag_suspicious_keywords(state.ROWS)
    return jsonify(state.LAST_RESULTS)

@app.route('/api/discrepancies')
def api_discrepancies():
    """Return payment discrepancies."""
    state.LAST_RESULTS = flag_discrepancies(state.ROWS)
    return jsonify(state.LAST_RESULTS)

@app.route('/download')
def download():
    """Download current results as CSV."""
    data = state.LAST_RESULTS if state.LAST_RESULTS else state.ROWS[:2000]
    fieldnames = sorted({k for r in data for k in r.keys()}) if data else []
    output = io.StringIO()
    if fieldnames:
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='expenses_audit_results.csv'
    )

# ===================================
# CRUD API Routes
# ===================================

@app.route('/api/add', methods=['POST'])
def api_add():
    """Add a new expense record."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        required_fields = ['expense_id', 'employee', 'department', 'expense_date', 
                          'amount_usd', 'currency', 'category', 'merchant', 'invoice_no']
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            return jsonify({'success': False, 'error': f'Missing fields: {", ".join(missing)}'}), 400
        
        if any(r.get('expense_id') == data.get('expense_id') for r in state.ROWS):
            return jsonify({'success': False, 'error': 'Expense ID already exists'}), 400
        
        try:
            datetime.strptime(data['expense_date'], '%Y-%m-%d')
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        if parse_float(data['amount_usd']) is None:
            return jsonify({'success': False, 'error': 'Invalid amount_usd'}), 400
        
        state.ROWS.append(data)
        
        if save_rows(state.CSV_PATH, state.ROWS):
            return jsonify({'success': True, 'message': 'Record added successfully'})
        else:
            state.ROWS.pop()
            return jsonify({'success': False, 'error': 'Failed to save to CSV'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/update/<expense_id>', methods=['PUT'])
def api_update(expense_id):
    """Update an existing expense record."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        index = None
        for i, row in enumerate(state.ROWS):
            if row.get('expense_id') == expense_id:
                index = i
                break
        
        if index is None:
            return jsonify({'success': False, 'error': 'Record not found'}), 404
        
        if 'expense_date' in data:
            try:
                datetime.strptime(data['expense_date'], '%Y-%m-%d')
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        if 'amount_usd' in data and parse_float(data['amount_usd']) is None:
            return jsonify({'success': False, 'error': 'Invalid amount_usd'}), 400
        
        old_data = dict(state.ROWS[index])
        state.ROWS[index].update(data)
        
        if save_rows(state.CSV_PATH, state.ROWS):
            return jsonify({'success': True, 'message': 'Record updated successfully'})
        else:
            state.ROWS[index] = old_data
            return jsonify({'success': False, 'error': 'Failed to save to CSV'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/delete/<expense_id>', methods=['DELETE'])
def api_delete(expense_id):
    """Delete an expense record."""
    try:
        index = None
        for i, row in enumerate(state.ROWS):
            if row.get('expense_id') == expense_id:
                index = i
                break
        
        if index is None:
            return jsonify({'success': False, 'error': 'Record not found'}), 404
        
        deleted_row = state.ROWS[index]
        del state.ROWS[index]
        
        if save_rows(state.CSV_PATH, state.ROWS):
            return jsonify({'success': True, 'message': 'Record deleted successfully'})
        else:
            state.ROWS.insert(index, deleted_row)
            return jsonify({'success': False, 'error': 'Failed to save to CSV'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/get/<expense_id>', methods=['GET'])
def api_get(expense_id):
    """Get a single expense record by ID."""
    for row in state.ROWS:
        if row.get('expense_id') == expense_id:
            return jsonify(row)
    return jsonify({'error': 'Record not found'}), 404

