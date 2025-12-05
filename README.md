# CS5001 Final Project: Expenses Audit

A professional forensic accounting and expense audit tool designed to detect fraud, compliance violations, and data anomalies in financial datasets.

## Project Overview

This application uses a modular Python application (MVC pattern), providing both a **Web Dashboard** for visual analysis and a **Command Line Interface (CLI)** for quick operations.

It implements **9 Core Functionalities** (exceeding the required 6), covering advanced audit algorithms and data management.

### Key Features

#### Audit & Analysis (Read)
1.  **Find Duplicate Invoices**: Detects potential double-billing fraud.
2.  **Flag Weekend Transactions**: Identifies compliance risks (expenses on Sat/Sun).
3.  **High-Value Thresholds**: Flags expenses exceeding policy limits.
4.  **Benford's Law Analysis**: Uses statistical distribution of leading digits to detect fabricated numbers.
5.  **Suspicious Keyword Scanner**: Detects high-risk terms (e.g., "casino", "gift", "cash").
6.  **Payment Discrepancies**: Checks if `Amount` matches `Paid Amount`.

#### Data Management (CRUD)
7.  **Add Record**: Create new entries with validation.
8.  **Update Record**: Modify existing entries.
9.  **Delete Record**: Remove erroneous entries safely.

---

## Project Structure(MVC Pattern)

The code is organized into a clean, modular structure for maintainability:

```text
project_root/
├── main.py                # Entry Point (Start here)
├── expenses_usa_2024.csv  # Data File
├── templates/
│   └── index.html         # Frontend UI (HTML/CSS/JS)
└── app/
    ├── __init__.py
    ├── auditor.py         # Core Audit Logic (Algorithms)
    ├── web.py             # Web Server Routes (Flask)
    ├── cli.py             # CLI Menu Logic
    ├── utils.py           # File I/O & Data Helpers
    └── state.py           # Global State Management
```

---

## How to Run

### 1. Prerequisites
*   **Python 3.7+**
*   **Flask** (Required for the web interface)

```bash
pip install flask
```

### 2. Running the Web Interface (Recommended)
The web dashboard features interactive charts (Benford Analysis) and a modern UI.

```bash
python3 main.py expenses_usa_2024.csv web
```
> **Then open your browser at:** http://127.0.0.1:5001

### 3. Running the CLI Menu
For text-based interaction in the terminal.

```bash
python3 main.py expenses_usa_2024.csv menu
```

### 4. Running Specific Commands
You can also run individual audit commands directly:

```bash
# Find duplicates
python3 main.py expenses_usa_2024.csv find-duplicates

# Run Benford's Law analysis
python3 main.py expenses_usa_2024.csv benford-analysis
```

---

## Error Handling & Safety

*   **Atomic Saves**: Data is saved to a `.tmp` file first and then moved. This prevents CSV corruption if the program crashes during a save.
*   **Input Validation**: All user inputs (Dates, Amounts) are strictly validated.
*   **Graceful Failures**: The application catches errors (e.g., malformed CSVs, invalid types) and reports them without crashing.
*   **Type Hinting**: The codebase uses Python type hinting (`List`, `Dict`, `Optional`) for better code quality and readability.

---


## Futere work

*   Move the system to a relational database like SQLite

---

## Thinking

 
AI can recite the definition of Benford's Law, but it didn't decide to apply it to this specific audit scenario—I did.

AI can write a file-save function, but it doesn't understand the panic and professional liability of losing client data—I do.

So, my takeaway is this: Use AI to move faster, but never use it to replace your professional judgment.

Be the Architect who designs the system; let AI be the Builder who lays the bricks. That is how we should use AI.


---

## Author
**Yanshi Liu**
11/30/2025
