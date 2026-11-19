-- =====================================================================
--  queries.sql  -  all reporting / business questions (SELECT only)
--  Format used by the Streamlit app:
--      -- name: <report title>
--      -- desc: <one-line description>
--      SELECT ...;
-- =====================================================================

-- name: 01. Total available copies in the library
-- desc: Aggregate function (SUM, COUNT)
SELECT  COUNT(*)              AS total_titles,
        SUM(total_copies)     AS total_copies,
        SUM(available_copies) AS available_copies,
        SUM(total_copies) - SUM(available_copies) AS currently_issued
FROM books;

-- name: 02. Availability per book
-- desc: ORDER BY on available copies
SELECT book_id, title, author, category, total_copies, available_copies
FROM books
ORDER BY available_copies DESC, title;

-- name: 03. Books that can be issued right now
-- desc: WHERE filter
SELECT book_id, title, author, available_copies
FROM books
WHERE available_copies > 0
ORDER BY title;

-- name: 04. Which member borrowed which book (full history)
-- desc: Three-table JOIN with CASE
SELECT  bi.issue_id,
        m.name  AS member_name,
        b.title AS book_title,
        bi.issue_date,
        bi.due_date,
        bi.return_date,
        CASE WHEN bi.return_date IS NULL THEN 'Issued' ELSE 'Returned' END AS status
FROM book_issues bi
JOIN members m ON bi.member_id = m.member_id
JOIN books   b ON bi.book_id   = b.book_id
ORDER BY bi.issue_date DESC;

-- name: 05. Books currently held by members
-- desc: JOIN + IS NULL check on return_date
SELECT  m.name AS member_name, b.title AS book_title,
        bi.issue_date, bi.due_date,
        DATEDIFF(bi.due_date, CURDATE()) AS days_left
FROM book_issues bi
JOIN members m ON bi.member_id = m.member_id
JOIN books   b ON bi.book_id   = b.book_id
WHERE bi.return_date IS NULL
ORDER BY m.name;

-- name: 06. Overdue books
-- desc: DATE function DATEDIFF / CURDATE
SELECT  bi.issue_id,
        m.name  AS member_name,
        m.email,
        b.title AS book_title,
        bi.due_date,
        DATEDIFF(CURDATE(), bi.due_date) AS days_overdue
FROM book_issues bi
JOIN members m ON bi.member_id = m.member_id
JOIN books   b ON bi.book_id   = b.book_id
WHERE bi.return_date IS NULL
  AND bi.due_date < CURDATE()
ORDER BY days_overdue DESC;

-- name: 07. Overdue books and late days per member
-- desc: GROUP BY with COUNT and SUM
SELECT  m.member_id, m.name,
        COUNT(*) AS overdue_books,
        SUM(DATEDIFF(CURDATE(), bi.due_date)) AS total_days_overdue
FROM book_issues bi
JOIN members m ON bi.member_id = m.member_id
WHERE bi.return_date IS NULL AND bi.due_date < CURDATE()
GROUP BY m.member_id, m.name
ORDER BY total_days_overdue DESC;

-- name: 08. Estimated fine for overdue books (Rs. 2 per day)
-- desc: Calculated column using DATEDIFF
SELECT  m.name AS member_name, b.title AS book_title,
        DATEDIFF(CURDATE(), bi.due_date)     AS days_overdue,
        DATEDIFF(CURDATE(), bi.due_date) * 2 AS fine_rupees
FROM book_issues bi
JOIN members m ON bi.member_id = m.member_id
JOIN books   b ON bi.book_id   = b.book_id
WHERE bi.return_date IS NULL AND bi.due_date < CURDATE()
ORDER BY fine_rupees DESC;

-- name: 09. Books that were returned late
-- desc: Comparing two date columns
SELECT  m.name AS member_name, b.title AS book_title,
        bi.due_date, bi.return_date,
        DATEDIFF(bi.return_date, bi.due_date) AS days_late
FROM book_issues bi
JOIN members m ON bi.member_id = m.member_id
JOIN books   b ON bi.book_id   = b.book_id
WHERE bi.return_date > bi.due_date
ORDER BY days_late DESC;

-- name: 10. Top 5 most borrowed books
-- desc: JOIN + GROUP BY + ORDER BY + LIMIT
SELECT  b.book_id, b.title, b.author,
        COUNT(bi.issue_id) AS times_borrowed
FROM books b
JOIN book_issues bi ON b.book_id = bi.book_id
GROUP BY b.book_id, b.title, b.author
ORDER BY times_borrowed DESC, b.title
LIMIT 5;

-- name: 11. Most active members
-- desc: GROUP BY member
SELECT  m.member_id, m.name, COUNT(bi.issue_id) AS books_borrowed
FROM members m
JOIN book_issues bi ON m.member_id = bi.member_id
GROUP BY m.member_id, m.name
ORDER BY books_borrowed DESC, m.name;

-- name: 12. Books never borrowed
-- desc: Subquery with NOT EXISTS
SELECT b.book_id, b.title, b.author
FROM books b
WHERE NOT EXISTS (
    SELECT 1 FROM book_issues bi WHERE bi.book_id = b.book_id
);

-- name: 13. Members who never borrowed a book
-- desc: Subquery with NOT IN
SELECT member_id, name, email, status
FROM members
WHERE member_id NOT IN (SELECT DISTINCT member_id FROM book_issues);

-- name: 14. Members who borrowed more than the average member
-- desc: Subquery in HAVING (nested aggregate)
SELECT  m.member_id, m.name, COUNT(*) AS books_borrowed
FROM members m
JOIN book_issues bi ON m.member_id = bi.member_id
GROUP BY m.member_id, m.name
HAVING COUNT(*) > (
    SELECT AVG(cnt)
    FROM (SELECT COUNT(*) AS cnt FROM book_issues GROUP BY member_id) AS t
)
ORDER BY books_borrowed DESC;

-- name: 15. Books more popular than the average book
-- desc: Subquery in HAVING
SELECT  b.book_id, b.title, COUNT(bi.issue_id) AS times_borrowed
FROM books b
JOIN book_issues bi ON b.book_id = bi.book_id
GROUP BY b.book_id, b.title
HAVING COUNT(bi.issue_id) > (
    SELECT AVG(cnt)
    FROM (SELECT COUNT(*) AS cnt FROM book_issues GROUP BY book_id) AS t
)
ORDER BY times_borrowed DESC;

-- name: 16. Borrowing by category
-- desc: GROUP BY category
SELECT  b.category, COUNT(*) AS total_issues,
        COUNT(DISTINCT bi.member_id) AS unique_members
FROM book_issues bi
JOIN books b ON bi.book_id = b.book_id
GROUP BY b.category
ORDER BY total_issues DESC;

-- name: 17. Monthly issue trend
-- desc: DATE_FORMAT with GROUP BY
SELECT DATE_FORMAT(issue_date, '%Y-%m') AS issue_month, COUNT(*) AS books_issued
FROM book_issues
GROUP BY DATE_FORMAT(issue_date, '%Y-%m')
ORDER BY DATE_FORMAT(issue_date, '%Y-%m');

-- name: 18. Books due in the next 7 days
-- desc: BETWEEN with DATE_ADD
SELECT  m.name AS member_name, b.title AS book_title, bi.due_date
FROM book_issues bi
JOIN members m ON bi.member_id = m.member_id
JOIN books   b ON bi.book_id   = b.book_id
WHERE bi.return_date IS NULL
  AND bi.due_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 7 DAY)
ORDER BY bi.due_date;

-- name: 19. Average days a book is kept before return
-- desc: AVG with DATEDIFF
SELECT  b.title,
        COUNT(*) AS returns,
        ROUND(AVG(DATEDIFF(bi.return_date, bi.issue_date)), 1) AS avg_days_kept
FROM book_issues bi
JOIN books b ON bi.book_id = b.book_id
WHERE bi.return_date IS NOT NULL
GROUP BY b.book_id, b.title
ORDER BY avg_days_kept DESC;

-- name: 20. Members who joined in the last 12 months
-- desc: Date filter on members
SELECT member_id, name, email, join_date, status
FROM members
WHERE join_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
ORDER BY join_date DESC;

-- name: 21. Inactive members still holding books
-- desc: JOIN + WHERE on two tables
SELECT DISTINCT m.member_id, m.name, b.title
FROM members m
JOIN book_issues bi ON m.member_id = bi.member_id
JOIN books b        ON bi.book_id  = b.book_id
WHERE m.status = 'inactive' AND bi.return_date IS NULL;

-- name: 22. Data integrity check (available vs actually issued)
-- desc: Should return zero rows when stock is consistent
SELECT  b.book_id, b.title, b.available_copies,
        b.total_copies - COUNT(bi.issue_id) AS expected_available
FROM books b
LEFT JOIN book_issues bi ON b.book_id = bi.book_id AND bi.return_date IS NULL
GROUP BY b.book_id, b.title, b.available_copies, b.total_copies
HAVING b.available_copies <> b.total_copies - COUNT(bi.issue_id);
