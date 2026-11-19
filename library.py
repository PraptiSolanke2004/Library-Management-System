"""
library.py - business logic: all CRUD, issue/return and delete-with-checks.

Every write function returns (success: bool, message: str).
Issue / return / delete run inside a transaction and use SELECT ... FOR UPDATE
so that available_copies can never go wrong.
"""
import re
from pathlib import Path

import mysql.connector
import pandas as pd

from db import execute, run_query, run_scalar, transaction

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class LibraryError(Exception):
    """Raised for business-rule violations (causes a rollback)."""


# =====================================================================
#  READ
# =====================================================================
def get_books() -> pd.DataFrame:
    return run_query("SELECT * FROM books ORDER BY book_id")


def search_books(text: str) -> pd.DataFrame:
    like = f"%{text}%"
    return run_query(
        """SELECT * FROM books
           WHERE title LIKE %s OR author LIKE %s OR category LIKE %s
           ORDER BY book_id""",
        (like, like, like),
    )


def get_available_books() -> pd.DataFrame:
    return run_query("SELECT * FROM books WHERE available_copies > 0 ORDER BY title")


def get_members() -> pd.DataFrame:
    return run_query("SELECT * FROM members ORDER BY member_id")


def get_active_members() -> pd.DataFrame:
    return run_query("SELECT * FROM members WHERE status = 'active' ORDER BY name")


def get_open_issues() -> pd.DataFrame:
    """Books that are currently issued (not yet returned)."""
    return run_query(
        """SELECT bi.issue_id, m.name AS member_name, b.title AS book_title,
                  bi.issue_date, bi.due_date,
                  GREATEST(DATEDIFF(CURDATE(), bi.due_date), 0) AS days_overdue
           FROM book_issues bi
           JOIN members m ON bi.member_id = m.member_id
           JOIN books   b ON bi.book_id   = b.book_id
           WHERE bi.return_date IS NULL
           ORDER BY bi.due_date"""
    )


def get_all_issues() -> pd.DataFrame:
    return run_query(
        """SELECT bi.issue_id, m.name AS member_name, b.title AS book_title,
                  bi.issue_date, bi.due_date, bi.return_date,
                  CASE WHEN bi.return_date IS NULL THEN 'Issued' ELSE 'Returned' END AS status
           FROM book_issues bi
           JOIN members m ON bi.member_id = m.member_id
           JOIN books   b ON bi.book_id   = b.book_id
           ORDER BY bi.issue_id DESC"""
    )


def dashboard_stats() -> dict:
    return {
        "titles": run_scalar("SELECT COUNT(*) FROM books"),
        "total_copies": run_scalar("SELECT COALESCE(SUM(total_copies), 0) FROM books"),
        "available": run_scalar("SELECT COALESCE(SUM(available_copies), 0) FROM books"),
        "members": run_scalar("SELECT COUNT(*) FROM members WHERE status = 'active'"),
        "issued": run_scalar("SELECT COUNT(*) FROM book_issues WHERE return_date IS NULL"),
        "overdue": run_scalar(
            "SELECT COUNT(*) FROM book_issues "
            "WHERE return_date IS NULL AND due_date < CURDATE()"
        ),
    }


# =====================================================================
#  CREATE
# =====================================================================
def add_book(title, author, category, copies):
    title, author, category = title.strip(), author.strip(), category.strip()
    if not title or not author:
        return False, "Title and author are required."
    if copies < 1:
        return False, "Copies must be at least 1."
    execute(
        """INSERT INTO books (title, author, category, total_copies, available_copies)
           VALUES (%s, %s, %s, %s, %s)""",
        (title, author, category or None, copies, copies),
    )
    return True, f"Book '{title}' added with {copies} copies."


def add_member(name, email, join_date, status="active"):
    name, email = name.strip(), email.strip().lower()
    if not name:
        return False, "Name is required."
    if not EMAIL_RE.match(email):
        return False, "Please enter a valid email address."
    try:
        execute(
            "INSERT INTO members (name, email, join_date, status) VALUES (%s, %s, %s, %s)",
            (name, email, join_date, status),
        )
    except mysql.connector.IntegrityError:
        return False, "A member with this email already exists."
    return True, f"Member '{name}' added."


# =====================================================================
#  UPDATE
# =====================================================================
def update_book_details(book_id, title, author, category):
    if not title.strip() or not author.strip():
        return False, "Title and author are required."
    execute(
        "UPDATE books SET title=%s, author=%s, category=%s WHERE book_id=%s",
        (title.strip(), author.strip(), category.strip() or None, book_id),
    )
    return True, "Book details updated."


def update_total_copies(book_id, new_total):
    """
    Change the total number of copies. Copies currently issued are kept,
    so available = new_total - issued. Cannot go below the issued count.
    """
    try:
        with transaction() as cur:
            cur.execute(
                "SELECT total_copies, available_copies FROM books WHERE book_id=%s FOR UPDATE",
                (book_id,),
            )
            row = cur.fetchone()
            if not row:
                raise LibraryError("Book not found.")
            issued = row["total_copies"] - row["available_copies"]
            if new_total < issued:
                raise LibraryError(
                    f"{issued} copies are currently issued; total cannot be below that."
                )
            cur.execute(
                "UPDATE books SET total_copies=%s, available_copies=%s WHERE book_id=%s",
                (new_total, new_total - issued, book_id),
            )
        return True, f"Total copies set to {new_total} ({new_total - issued} available)."
    except LibraryError as e:
        return False, str(e)


def update_member(member_id, name, email, status):
    if not name.strip():
        return False, "Name is required."
    if not EMAIL_RE.match(email.strip()):
        return False, "Please enter a valid email address."
    try:
        execute(
            "UPDATE members SET name=%s, email=%s, status=%s WHERE member_id=%s",
            (name.strip(), email.strip().lower(), status, member_id),
        )
    except mysql.connector.IntegrityError:
        return False, "Another member already uses this email."
    return True, "Member updated."


# =====================================================================
#  ISSUE / RETURN
# =====================================================================
def issue_book(book_id, member_id, days=14):
    try:
        with transaction() as cur:
            cur.execute("SELECT status FROM members WHERE member_id=%s", (member_id,))
            member = cur.fetchone()
            if not member:
                raise LibraryError("Member not found.")
            if member["status"] != "active":
                raise LibraryError("Member is inactive and cannot borrow books.")

            # Lock the book row so two librarians can't take the last copy together
            cur.execute(
                "SELECT title, available_copies FROM books WHERE book_id=%s FOR UPDATE",
                (book_id,),
            )
            book = cur.fetchone()
            if not book:
                raise LibraryError("Book not found.")
            if book["available_copies"] <= 0:
                raise LibraryError("No copies available right now.")

            cur.execute(
                """SELECT COUNT(*) AS c FROM book_issues
                   WHERE book_id=%s AND member_id=%s AND return_date IS NULL""",
                (book_id, member_id),
            )
            if cur.fetchone()["c"] > 0:
                raise LibraryError("This member already has this book.")

            cur.execute(
                """INSERT INTO book_issues (book_id, member_id, issue_date, due_date)
                   VALUES (%s, %s, CURDATE(), DATE_ADD(CURDATE(), INTERVAL %s DAY))""",
                (book_id, member_id, days),
            )
            cur.execute(
                "UPDATE books SET available_copies = available_copies - 1 WHERE book_id=%s",
                (book_id,),
            )
        return True, f"'{book['title']}' issued for {days} days."
    except LibraryError as e:
        return False, str(e)


def return_book(issue_id):
    try:
        with transaction() as cur:
            cur.execute(
                """SELECT book_id, due_date, return_date,
                          DATEDIFF(CURDATE(), due_date) AS late_days
                   FROM book_issues WHERE issue_id=%s FOR UPDATE""",
                (issue_id,),
            )
            issue = cur.fetchone()
            if not issue:
                raise LibraryError("Issue record not found.")
            if issue["return_date"] is not None:
                raise LibraryError("This book was already returned.")

            cur.execute(
                "UPDATE book_issues SET return_date = CURDATE() WHERE issue_id=%s", (issue_id,)
            )
            cur.execute(
                "UPDATE books SET available_copies = available_copies + 1 WHERE book_id=%s",
                (issue["book_id"],),
            )
        late = max(issue["late_days"], 0)
        if late:
            return True, f"Book returned. It was {late} day(s) late (fine: Rs. {late * 2})."
        return True, "Book returned on time."
    except LibraryError as e:
        return False, str(e)


# =====================================================================
#  DELETE (with checks)
# =====================================================================
def delete_member(member_id):
    """
    - refuse if member still has unreturned books
    - if member has history, mark inactive (history must be preserved)
    - otherwise delete the row
    """
    try:
        with transaction() as cur:
            cur.execute("SELECT name FROM members WHERE member_id=%s FOR UPDATE", (member_id,))
            member = cur.fetchone()
            if not member:
                raise LibraryError("Member not found.")

            cur.execute(
                "SELECT COUNT(*) AS pending FROM book_issues "
                "WHERE member_id=%s AND return_date IS NULL",
                (member_id,),
            )
            if cur.fetchone()["pending"] > 0:
                raise LibraryError("Member still has unreturned books. Cannot delete.")

            cur.execute(
                "SELECT COUNT(*) AS hist FROM book_issues WHERE member_id=%s", (member_id,)
            )
            if cur.fetchone()["hist"] > 0:
                cur.execute(
                    "UPDATE members SET status='inactive' WHERE member_id=%s", (member_id,)
                )
                return True, (
                    f"{member['name']} has borrowing history, so the account was "
                    "marked inactive instead of deleted."
                )
            cur.execute("DELETE FROM members WHERE member_id=%s", (member_id,))
        return True, f"Member '{member['name']}' deleted."
    except LibraryError as e:
        return False, str(e)


def delete_book(book_id):
    """
    - refuse if any copy is currently issued
    - if the book has history, set stock to 0 (history must be preserved)
    - otherwise delete the row
    """
    try:
        with transaction() as cur:
            cur.execute("SELECT title FROM books WHERE book_id=%s FOR UPDATE", (book_id,))
            book = cur.fetchone()
            if not book:
                raise LibraryError("Book not found.")

            cur.execute(
                "SELECT COUNT(*) AS pending FROM book_issues "
                "WHERE book_id=%s AND return_date IS NULL",
                (book_id,),
            )
            if cur.fetchone()["pending"] > 0:
                raise LibraryError("Some copies are currently issued. Cannot delete.")

            cur.execute("SELECT COUNT(*) AS hist FROM book_issues WHERE book_id=%s", (book_id,))
            if cur.fetchone()["hist"] > 0:
                cur.execute(
                    "UPDATE books SET total_copies=0, available_copies=0 WHERE book_id=%s",
                    (book_id,),
                )
                return True, (
                    f"'{book['title']}' has issue history, so its stock was set to 0 "
                    "instead of deleting the record."
                )
            cur.execute("DELETE FROM books WHERE book_id=%s", (book_id,))
        return True, f"Book '{book['title']}' deleted."
    except LibraryError as e:
        return False, str(e)


# =====================================================================
#  REPORTS  (loaded from queries.sql)
# =====================================================================
def load_reports(path=None) -> list[dict]:
    """
    Parse queries.sql into [{'name', 'desc', 'sql'}, ...].
    Each report starts with '-- name:' and ends at the first ';'.
    """
    path = Path(path) if path else Path(__file__).with_name("queries.sql")
    reports, current = [], None
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("-- name:"):
            current = {"name": stripped[8:].strip(), "desc": "", "sql": ""}
            reports.append(current)
        elif current is not None:
            if stripped.startswith("-- desc:"):
                current["desc"] = stripped[8:].strip()
            elif stripped.startswith("--") or not stripped:
                continue
            else:
                current["sql"] += line + "\n"
    for r in reports:
        r["sql"] = r["sql"].strip().rstrip(";")
    return reports


def run_report(sql: str) -> pd.DataFrame:
    return run_query(sql)


# =====================================================================
#  DASHBOARD DATA  (charts, overdue list, recent activity)
# =====================================================================
def dashboard_data() -> dict:
    return {
        "top_books": run_query(
            """SELECT b.title, COUNT(*) AS times_borrowed
               FROM book_issues bi
               JOIN books b ON bi.book_id = b.book_id
               GROUP BY b.book_id, b.title
               ORDER BY times_borrowed DESC, b.title
               LIMIT 5"""
        ),
        "categories": run_query(
            """SELECT COALESCE(b.category, 'Uncategorized') AS category, COUNT(*) AS issues
               FROM book_issues bi
               JOIN books b ON bi.book_id = b.book_id
               GROUP BY COALESCE(b.category, 'Uncategorized')
               ORDER BY issues DESC"""
        ),
        "monthly": run_query(
            """SELECT DATE_FORMAT(issue_date, '%Y-%m') AS month, COUNT(*) AS issues
               FROM book_issues
               GROUP BY DATE_FORMAT(issue_date, '%Y-%m')
               ORDER BY DATE_FORMAT(issue_date, '%Y-%m')"""
        ),
        "overdue": run_query(
            """SELECT m.name AS member, b.title AS book, bi.due_date,
                      DATEDIFF(CURDATE(), bi.due_date)     AS days_overdue,
                      DATEDIFF(CURDATE(), bi.due_date) * 2 AS fine_rs
               FROM book_issues bi
               JOIN members m ON bi.member_id = m.member_id
               JOIN books   b ON bi.book_id   = b.book_id
               WHERE bi.return_date IS NULL AND bi.due_date < CURDATE()
               ORDER BY days_overdue DESC"""
        ),
        "recent": run_query(
            """SELECT m.name AS member, b.title AS book, bi.issue_date, bi.return_date,
                      CASE WHEN bi.return_date IS NULL THEN 'Issued' ELSE 'Returned' END AS status
               FROM book_issues bi
               JOIN members m ON bi.member_id = m.member_id
               JOIN books   b ON bi.book_id   = b.book_id
               ORDER BY bi.issue_id DESC
               LIMIT 6"""
        ),
    }
