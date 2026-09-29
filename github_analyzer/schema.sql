CREATE TABLE IF NOT EXISTS commits (
    sha TEXT PRIMARY KEY,
    repo TEXT,
    author TEXT,
    date TEXT,
    message TEXT
);

CREATE TABLE IF NOT EXISTS pull_requests (
    id INTEGER PRIMARY KEY,
    repo TEXT,
    number INTEGER,
    title TEXT,
    state TEXT,
    created_at TEXT,
    closed_at TEXT,
    author TEXT
);

CREATE TABLE IF NOT EXISTS issues (
    id INTEGER PRIMARY KEY,
    repo TEXT,
    number INTEGER,
    title TEXT,
    state TEXT,
    created_at TEXT,
    closed_at TEXT,
    author TEXT,
    comments INTEGER
);