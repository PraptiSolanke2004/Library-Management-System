-- =====================================================================
--  LIBRARY MANAGEMENT SYSTEM  -  schema.sql   (MySQL 8.0.16+)
--  Creates the database, tables, constraints, indexes and sample data.
--  Run with:  python init_db.py     (or)     mysql -u root -p < schema.sql
-- =====================================================================

DROP DATABASE IF EXISTS library_db;
CREATE DATABASE library_db;
USE library_db;

-- ---------------------------------------------------------------------
-- TABLE 1: books
-- ---------------------------------------------------------------------
CREATE TABLE books (
    book_id          INT PRIMARY KEY AUTO_INCREMENT,
    title            VARCHAR(100) NOT NULL,
    author           VARCHAR(100) NOT NULL,
    category         VARCHAR(50),
    total_copies     INT NOT NULL DEFAULT 1,
    available_copies INT NOT NULL DEFAULT 1,
    CONSTRAINT chk_total_copies       CHECK (total_copies >= 0),
    CONSTRAINT chk_available_ge0      CHECK (available_copies >= 0),
    CONSTRAINT chk_available_le_total CHECK (available_copies <= total_copies)
);

-- ---------------------------------------------------------------------
-- TABLE 2: members
-- ---------------------------------------------------------------------
CREATE TABLE members (
    member_id  INT PRIMARY KEY AUTO_INCREMENT,
    name       VARCHAR(100) NOT NULL,
    email      VARCHAR(100) NOT NULL UNIQUE,
    join_date  DATE NOT NULL,
    status     ENUM('active', 'inactive') NOT NULL DEFAULT 'active'
);

-- ---------------------------------------------------------------------
-- TABLE 3: book_issues   (links books <-> members)
-- ---------------------------------------------------------------------
CREATE TABLE book_issues (
    issue_id    INT PRIMARY KEY AUTO_INCREMENT,
    book_id     INT NOT NULL,
    member_id   INT NOT NULL,
    issue_date  DATE NOT NULL,
    due_date    DATE NOT NULL,
    return_date DATE NULL,
    CONSTRAINT fk_issue_book   FOREIGN KEY (book_id)   REFERENCES books(book_id),
    CONSTRAINT fk_issue_member FOREIGN KEY (member_id) REFERENCES members(member_id),
    CONSTRAINT chk_due_after_issue    CHECK (due_date >= issue_date),
    CONSTRAINT chk_return_after_issue CHECK (return_date IS NULL OR return_date >= issue_date)
);

CREATE INDEX idx_issues_book   ON book_issues(book_id);
CREATE INDEX idx_issues_member ON book_issues(member_id);
CREATE INDEX idx_issues_due    ON book_issues(due_date, return_date);

-- ---------------------------------------------------------------------
-- SAMPLE DATA
-- ---------------------------------------------------------------------
INSERT INTO books (title, author, category, total_copies, available_copies) VALUES
('Python Crash Course',                  'Eric Matthes',        'Python', 5, 5),
('Automate the Boring Stuff with Python','Al Sweigart',         'Python', 4, 4),
('Fluent Python',                        'Luciano Ramalho',     'Python', 3, 3),
('Learning Python',                      'Mark Lutz',           'Python', 3, 3),
('Think Python',                         'Allen B. Downey',     'Python', 4, 4),
('Effective Python',                     'Brett Slatkin',       'Python', 2, 2),
('Learning SQL',                         'Alan Beaulieu',       'SQL', 4, 4),
('SQL in 10 Minutes, Sams Teach Yourself','Ben Forta',          'SQL', 5, 5),
('SQL Cookbook',                         'Anthony Molinaro',    'SQL', 3, 3),
('Head First SQL',                       'Lynn Beighley',       'SQL', 3, 3),
('SQL Queries for Mere Mortals',         'John L. Viescas',     'SQL', 3, 3),
('Practical SQL',                        'Anthony DeBarros',    'SQL', 4, 4),
('SQL Performance Explained',            'Markus Winand',       'SQL', 2, 2),
('SQL for Smarties',                     'Joe Celko',           'SQL', 2, 2),
('Python Data Science Handbook',         'Jake VanderPlas',     'Data Science', 4, 4),
('Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow',
                                         'Aurelien Geron',      'Data Science', 4, 4),
('Data Science from Scratch',            'Joel Grus',           'Data Science', 3, 3),
('An Introduction to Statistical Learning','Gareth James',      'Data Science', 3, 3),
('Practical Statistics for Data Scientists','Peter Bruce',      'Data Science', 3, 3),
('Deep Learning',                        'Ian Goodfellow',      'Data Science', 2, 2),
('The Elements of Statistical Learning', 'Trevor Hastie',       'Data Science', 2, 2),
('Data Science for Business',            'Foster Provost',      'Data Science', 3, 3),
('Python for Data Analysis',             'Wes McKinney',        'Data Analytics', 5, 5),
('Storytelling with Data',               'Cole Nussbaumer Knaflic','Data Analytics', 4, 4),
('Naked Statistics',                     'Charles Wheelan',     'Data Analytics', 3, 3),
('Data Analytics Made Accessible',       'Anil Maheshwari',     'Data Analytics', 3, 3),
('The Data Warehouse Toolkit',           'Ralph Kimball',       'Data Analytics', 2, 2),
('Competing on Analytics',               'Thomas H. Davenport', 'Data Analytics', 2, 2);

INSERT INTO members (name, email, join_date, status) VALUES
('Prapti Solanke',   'prapti.solanke@gmail.com',   '2024-01-15', 'active'),
('Vishal Patil',    'vishal.patil@gmail.com',    '2024-03-10', 'active'),
('Vaishnavi Patil', 'vaishnavi.patil@gmail.com', '2024-05-22', 'active'),
('Preash Mahajan', 'paresh.mahajan@gmail.com', '2024-07-01', 'active'),
('Prajwal shukla',   'prajwal.shukla@gmail.com',   '2023-11-30', 'inactive'),
('lina patil',     'lina.vp@gmail.com',     '2025-01-05', 'active');

-- Dates are relative to today, so overdue reports always have data
INSERT INTO book_issues (book_id, member_id, issue_date, due_date, return_date) VALUES
-- returned
(1, 1, DATE_SUB(CURDATE(), INTERVAL 60 DAY), DATE_SUB(CURDATE(), INTERVAL 46 DAY), DATE_SUB(CURDATE(), INTERVAL 48 DAY)),
(3, 2, DATE_SUB(CURDATE(), INTERVAL 50 DAY), DATE_SUB(CURDATE(), INTERVAL 36 DAY), DATE_SUB(CURDATE(), INTERVAL 30 DAY)),
(7, 3, DATE_SUB(CURDATE(), INTERVAL 40 DAY), DATE_SUB(CURDATE(), INTERVAL 26 DAY), DATE_SUB(CURDATE(), INTERVAL 28 DAY)),
(1, 4, DATE_SUB(CURDATE(), INTERVAL 35 DAY), DATE_SUB(CURDATE(), INTERVAL 21 DAY), DATE_SUB(CURDATE(), INTERVAL 22 DAY)),
(7, 1, DATE_SUB(CURDATE(), INTERVAL 30 DAY), DATE_SUB(CURDATE(), INTERVAL 16 DAY), DATE_SUB(CURDATE(), INTERVAL 15 DAY)),
-- issued and overdue
(3, 1, DATE_SUB(CURDATE(), INTERVAL 25 DAY), DATE_SUB(CURDATE(), INTERVAL 11 DAY), NULL),
(4, 2, DATE_SUB(CURDATE(), INTERVAL 20 DAY), DATE_SUB(CURDATE(), INTERVAL 6 DAY),  NULL),
(2, 3, DATE_SUB(CURDATE(), INTERVAL 18 DAY), DATE_SUB(CURDATE(), INTERVAL 4 DAY),  NULL),
-- issued, not yet due
(1, 6, DATE_SUB(CURDATE(), INTERVAL 5 DAY),  DATE_ADD(CURDATE(), INTERVAL 9 DAY),  NULL),
(7, 4, DATE_SUB(CURDATE(), INTERVAL 3 DAY),  DATE_ADD(CURDATE(), INTERVAL 11 DAY), NULL),
(6, 2, DATE_SUB(CURDATE(), INTERVAL 2 DAY),  DATE_ADD(CURDATE(), INTERVAL 12 DAY), NULL),
(1, 3, DATE_SUB(CURDATE(), INTERVAL 1 DAY),  DATE_ADD(CURDATE(), INTERVAL 13 DAY), NULL);

-- Keep available_copies in sync with currently issued books (correlated subquery)
UPDATE books b
SET b.available_copies = b.total_copies - (
    SELECT COUNT(*) FROM book_issues bi
    WHERE bi.book_id = b.book_id AND bi.return_date IS NULL
);
