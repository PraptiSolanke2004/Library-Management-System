# Library Management System (Python + MySQL + Streamlit)

## Project structure

| File | Purpose |
|------|---------|
| `schema.sql` | Database, tables, PK/FK/CHECK/UNIQUE constraints, indexes, sample data |
| `queries.sql` | 22 reporting queries (JOIN, GROUP BY, ORDER BY, aggregates, subqueries, date functions) |
| `db.py` | MySQL connection, `run_query`, `execute`, `transaction()` helper |
| `library.py` | Business logic: CRUD, issue/return, delete-with-checks, report loader |
| `init_db.py` | Runs `schema.sql` to set up the database |
| `app.py` | Streamlit UI (forms, buttons, pages) |
| `theme.py` | Custom CSS: background image, KPI cards, sidebar styling |
| `assets/background.svg` | Default background image |
| `.streamlit/config.toml` | Streamlit theme settings |

## Setup

1. Install MySQL 8.0.16 or later and make sure it is running.
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. (Optional) set connection details if they differ from the defaults
   (`localhost`, port `3306`, user `root`, empty password):
   ```
   # Windows (PowerShell)
   $env:DB_USER="root"; $env:DB_PASSWORD="your_password"
   # macOS / Linux
   export DB_USER=root DB_PASSWORD=your_password
   ```
4. Create the database and load sample data:
   ```
   python init_db.py
   ```
   (Running this again resets the database to the sample data.)
5. Start the app:
   ```
   streamlit run app.py
   ```

## What the app does

- **Dashboard**: totals, available copies, issued and overdue counts.
- **Books**: search, add, edit details, update quantity, delete with checks.
- **Members**: view, add, edit, delete with checks.
- **Issue / Return**: issue (checks active member, stock, duplicate loan) and return (shows late days and fine).
- **Reports (SQL)**: pick any query from `queries.sql`, see the SQL, the result table and download a CSV.

## Business rules

- A book cannot be issued if `available_copies = 0`; the database CHECK constraints also prevent negative stock.
- Inactive members cannot borrow.
- A member cannot hold two copies of the same title at once.
- Members or books with unreturned copies cannot be deleted.
- Members or books with past history are deactivated / zero-stocked instead of deleted, so the history stays intact.
- Fine is Rs. 2 per overdue day (used in the return message and query 08).

## Adding your own report

Add a block to `queries.sql` and it shows up in the Reports page automatically:

```sql
-- name: 23. My new report
-- desc: What it shows
SELECT ... ;
```

## Changing the background image

Put your own picture in the `assets` folder and name it `background.jpg`
(or `.png`, `.webp`). It is picked up automatically and takes priority over the
default `background.svg`. Restart the app after changing it.
