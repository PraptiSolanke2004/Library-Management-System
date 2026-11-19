"""
app.py - Streamlit UI for the Library Management System.
Run with:  streamlit run app.py
"""
import datetime as dt

import streamlit as st

import library as lib
from theme import apply_theme, kpi_card, sidebar_brand

st.set_page_config(page_title="Library Management System", page_icon="📚", layout="wide")
apply_theme()


def show(result):
    """Display a (success, message) tuple from library.py."""
    ok, msg = result
    (st.success if ok else st.error)(msg)
    return ok


def book_label(row):
    return f"#{row.book_id}  {row.title}  ({row.available_copies}/{row.total_copies} available)"


def member_label(row):
    return f"#{row.member_id}  {row['name']}  [{row.status}]"


# ---------------------------------------------------------------------
# Connection check
# ---------------------------------------------------------------------
try:
    stats = lib.dashboard_stats()
except Exception as e:
    st.title("📚 Library Management System")
    st.error(f"Could not connect to MySQL: {e}")
    st.info(
        "1. Make sure MySQL is running.\n"
        "2. Run `python init_db.py` to create the database.\n"
        "3. Set DB_HOST, DB_USER, DB_PASSWORD environment variables if needed."
    )
    st.stop()

sidebar_brand()
page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Books", "Members", "Issue / Return", "Reports (SQL)"],
)
st.sidebar.caption("Python + MySQL + Streamlit")

# =====================================================================
# DASHBOARD
# =====================================================================
if page == "Dashboard":
    data = lib.dashboard_data()
    today = dt.date.today().strftime("%A, %d %B %Y")

    # ---- hero banner ----
    st.markdown(
        f'<div class="hero"><h1>Library Dashboard</h1>'
        f'<p>{today} &nbsp;|&nbsp; {stats["issued"]} books out, '
        f'{stats["overdue"]} overdue</p></div>',
        unsafe_allow_html=True,
    )

    # ---- KPI cards ----
    cards = [
        kpi_card("📘", "Book titles", stats["titles"], "linear-gradient(135deg,#6366f1,#4338ca)"),
        kpi_card("📚", "Total copies", int(stats["total_copies"]), "linear-gradient(135deg,#0ea5e9,#0369a1)"),
        kpi_card("✅", "Available copies", int(stats["available"]), "linear-gradient(135deg,#10b981,#047857)"),
        kpi_card("👥", "Active members", stats["members"], "linear-gradient(135deg,#8b5cf6,#6d28d9)"),
        kpi_card("📤", "Currently issued", stats["issued"], "linear-gradient(135deg,#f59e0b,#b45309)"),
        kpi_card("⏰", "Overdue", stats["overdue"], "linear-gradient(135deg,#ef4444,#b91c1c)"),
    ]
    st.markdown('<div class="kpi-grid">' + "".join(cards) + "</div>", unsafe_allow_html=True)

    # ---- stock availability bar ----
    total = int(stats["total_copies"]) or 1
    avail = int(stats["available"])
    pct = round(avail / total * 100)
    with st.container(border=True):
        st.markdown('<div class="section-title">Stock availability</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="avail-wrap"><div class="avail-bar">'
            f'<div class="avail-fill" style="width:{pct}%"></div></div>'
            f'<div class="avail-text"><span>{avail} of {total} copies on the shelf</span>'
            f"<span><b>{pct}%</b> available</span></div></div>",
            unsafe_allow_html=True,
        )

    # ---- charts row 1 ----
    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            st.markdown('<div class="section-title">Top 5 most borrowed books</div>', unsafe_allow_html=True)
            if data["top_books"].empty:
                st.info("No borrowing data yet.")
            else:
                st.bar_chart(data["top_books"], x="title", y="times_borrowed", color="#6366f1", height=280)
    with right:
        with st.container(border=True):
            st.markdown('<div class="section-title">Borrowing by category</div>', unsafe_allow_html=True)
            if data["categories"].empty:
                st.info("No borrowing data yet.")
            else:
                st.bar_chart(data["categories"], x="category", y="issues", color="#ec4899", height=280)

    # ---- charts row 2 ----
    left, right = st.columns([3, 2])
    with left:
        with st.container(border=True):
            st.markdown('<div class="section-title">Monthly issue trend</div>', unsafe_allow_html=True)
            if data["monthly"].empty:
                st.info("No borrowing data yet.")
            else:
                st.area_chart(data["monthly"], x="month", y="issues", color="#0ea5e9", height=250)
    with right:
        with st.container(border=True):
            st.markdown('<div class="section-title">Recent activity</div>', unsafe_allow_html=True)
            if data["recent"].empty:
                st.info("No transactions yet.")
            else:
                rows = ""
                for r in data["recent"].itertuples():
                    cls = r.status.lower()
                    when = r.return_date if r.status == "Returned" else r.issue_date
                    rows += (
                        f'<div class="feed-item"><span class="badge {cls}">{r.status}</span>'
                        f'<div><div>{r.book}</div>'
                        f'<div class="feed-sub">{r.member} &middot; {when}</div></div></div>'
                    )
                st.markdown(rows, unsafe_allow_html=True)

    # ---- overdue table ----
    with st.container(border=True):
        st.markdown('<div class="section-title">Overdue books</div>', unsafe_allow_html=True)
        if data["overdue"].empty:
            st.success("No overdue books. Everything is on time.")
        else:
            st.dataframe(
                data["overdue"].rename(columns={
                    "member": "Member", "book": "Book", "due_date": "Due date",
                    "days_overdue": "Days overdue", "fine_rs": "Fine (Rs.)",
                }),
                use_container_width=True, hide_index=True,
            )

# =====================================================================
# BOOKS
# =====================================================================
elif page == "Books":
    st.title("📖 Books")
    tab_view, tab_add, tab_edit, tab_del = st.tabs(["View / Search", "Add", "Update", "Delete"])

    with tab_view:
        text = st.text_input("Search by title, author or category")
        df = lib.search_books(text) if text else lib.get_books()
        st.dataframe(df, use_container_width=True, hide_index=True)

    with tab_add:
        with st.form("add_book", clear_on_submit=True):
            title = st.text_input("Title")
            author = st.text_input("Author")
            category = st.text_input("Category")
            copies = st.number_input("Number of copies", min_value=1, value=1, step=1)
            if st.form_submit_button("Add book"):
                show(lib.add_book(title, author, category, int(copies)))

    books = lib.get_books()

    with tab_edit:
        if books.empty:
            st.info("No books yet.")
        else:
            options = {book_label(r): r for r in books.itertuples()}
            sel = options[st.selectbox("Select a book", list(options), key="edit_book")]

            st.markdown("**Edit details**")
            with st.form("edit_book_details"):
                t = st.text_input("Title", sel.title)
                a = st.text_input("Author", sel.author)
                c = st.text_input("Category", sel.category or "")
                if st.form_submit_button("Save details"):
                    show(lib.update_book_details(sel.book_id, t, a, c))

            st.markdown("**Update quantity**")
            with st.form("edit_book_qty"):
                new_total = st.number_input(
                    "Total copies", min_value=0, value=int(sel.total_copies), step=1
                )
                if st.form_submit_button("Update quantity"):
                    show(lib.update_total_copies(sel.book_id, int(new_total)))

    with tab_del:
        if books.empty:
            st.info("No books yet.")
        else:
            options = {book_label(r): r.book_id for r in books.itertuples()}
            label = st.selectbox("Select a book to delete", list(options), key="del_book")
            st.warning("Books with borrowing history keep their record; only the stock is set to 0.")
            if st.button("Delete book", type="primary"):
                show(lib.delete_book(options[label]))

# =====================================================================
# MEMBERS
# =====================================================================
elif page == "Members":
    st.title("👥 Members")
    tab_view, tab_add, tab_edit, tab_del = st.tabs(["View", "Add", "Update", "Delete"])

    with tab_view:
        st.dataframe(lib.get_members(), use_container_width=True, hide_index=True)

    with tab_add:
        with st.form("add_member", clear_on_submit=True):
            name = st.text_input("Full name")
            email = st.text_input("Email")
            joined = st.date_input("Join date", value=dt.date.today())
            status = st.selectbox("Status", ["active", "inactive"])
            if st.form_submit_button("Add member"):
                show(lib.add_member(name, email, joined, status))

    members = lib.get_members()

    with tab_edit:
        if members.empty:
            st.info("No members yet.")
        else:
            options = {member_label(r): r for _, r in members.iterrows()}
            sel = options[st.selectbox("Select a member", list(options), key="edit_member")]
            with st.form("edit_member_form"):
                n = st.text_input("Name", sel["name"])
                e = st.text_input("Email", sel["email"])
                s = st.selectbox(
                    "Status", ["active", "inactive"],
                    index=0 if sel["status"] == "active" else 1,
                )
                if st.form_submit_button("Save changes"):
                    show(lib.update_member(int(sel["member_id"]), n, e, s))

    with tab_del:
        if members.empty:
            st.info("No members yet.")
        else:
            options = {member_label(r): int(r["member_id"]) for _, r in members.iterrows()}
            label = st.selectbox("Select a member to delete", list(options), key="del_member")
            st.warning(
                "Members with unreturned books cannot be deleted. "
                "Members with history are marked inactive instead."
            )
            if st.button("Delete member", type="primary"):
                show(lib.delete_member(options[label]))

# =====================================================================
# ISSUE / RETURN
# =====================================================================
elif page == "Issue / Return":
    st.title("🔄 Issue & Return")
    tab_issue, tab_return, tab_hist = st.tabs(["Issue a book", "Return a book", "All transactions"])

    with tab_issue:
        members = lib.get_active_members()
        books = lib.get_available_books()
        if members.empty or books.empty:
            st.info("Need at least one active member and one available book.")
        else:
            m_opts = {member_label(r): int(r["member_id"]) for _, r in members.iterrows()}
            b_opts = {book_label(r): r.book_id for r in books.itertuples()}
            with st.form("issue_form"):
                m_label = st.selectbox("Member", list(m_opts))
                b_label = st.selectbox("Book", list(b_opts))
                days = st.number_input("Loan period (days)", min_value=1, max_value=60, value=14)
                if st.form_submit_button("Issue book"):
                    show(lib.issue_book(b_opts[b_label], m_opts[m_label], int(days)))

    with tab_return:
        open_issues = lib.get_open_issues()
        if open_issues.empty:
            st.info("No books are waiting to be returned.")
        else:
            opts = {
                f"#{r.issue_id}  {r.book_title}  -  {r.member_name}  "
                f"(due {r.due_date}{', OVERDUE ' + str(r.days_overdue) + 'd' if r.days_overdue else ''})":
                r.issue_id
                for r in open_issues.itertuples()
            }
            label = st.selectbox("Select issued book", list(opts))
            if st.button("Return book", type="primary"):
                show(lib.return_book(int(opts[label])))

    with tab_hist:
        st.dataframe(lib.get_all_issues(), use_container_width=True, hide_index=True)

# =====================================================================
# REPORTS
# =====================================================================
else:
    st.title("📊 SQL Reports")
    reports = lib.load_reports()
    names = [r["name"] for r in reports]
    choice = st.selectbox("Choose a report", names)
    report = reports[names.index(choice)]

    if report["desc"]:
        st.caption(report["desc"])
    st.code(report["sql"], language="sql")

    try:
        result = lib.run_report(report["sql"])
        if result.empty:
            st.info("This query returned no rows.")
        else:
            st.dataframe(result, use_container_width=True, hide_index=True)
            st.download_button(
                "Download CSV", result.to_csv(index=False), file_name="report.csv", mime="text/csv"
            )
    except Exception as e:
        st.error(f"Query failed: {e}")
