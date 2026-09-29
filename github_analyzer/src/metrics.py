import sqlite3
from pathlib import Path

import pandas as pd


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

DB_PATH = (
    PROJECT_ROOT
    / "data"
    / "gitpulse.db"
)


def get_connection():
    """Create a connection to the GitPulse SQLite database."""

    return sqlite3.connect(DB_PATH)


def commit_frequency(conn, repo):
    """Return weekly commit counts for a repository."""

    df = pd.read_sql(
        """
        SELECT date
        FROM commits
        WHERE repo = ?
        """,
        conn,
        params=(repo,)
    )

    if df.empty:
        return pd.Series(dtype="int64")

    df["date"] = pd.to_datetime(
        df["date"],
        utc=True,
        errors="coerce"
    )

    df = df.dropna(
        subset=["date"]
    )

    if df.empty:
        return pd.Series(dtype="int64")

    df["week"] = (
        df["date"]
        .dt.tz_localize(None)
        .dt.to_period("W")
    )

    return df.groupby("week").size()


def commits_last_30_days(repo):
    """Return commits made during the last 30 days."""

    conn = get_connection()

    try:
        df = pd.read_sql(
            """
            SELECT date
            FROM commits
            WHERE repo = ?
            """,
            conn,
            params=(repo,)
        )
    finally:
        conn.close()

    if df.empty:
        return 0

    df["date"] = pd.to_datetime(
        df["date"],
        utc=True,
        errors="coerce"
    )

    cutoff = (
        pd.Timestamp.now(tz="UTC")
        - pd.Timedelta(days=30)
    )

    return int(
        (df["date"] > cutoff).sum()
    )


def contributor_retention(
    conn,
    repo,
    days=90
):
    """Return unique contributors active in the last N days."""

    df = pd.read_sql(
        """
        SELECT author, date
        FROM commits
        WHERE repo = ?
        """,
        conn,
        params=(repo,)
    )

    if df.empty:
        return 0

    df["date"] = pd.to_datetime(
        df["date"],
        utc=True,
        errors="coerce"
    )

    cutoff = (
        pd.Timestamp.now(tz="UTC")
        - pd.Timedelta(days=days)
    )

    recent = df[
        df["date"] > cutoff
    ]

    return int(
        recent["author"]
        .dropna()
        .nunique()
    )


def active_contributors(
    repo,
    days=90
):
    """Return unique contributors active in the last N days."""

    conn = get_connection()

    try:
        return contributor_retention(
            conn,
            repo,
            days
        )
    finally:
        conn.close()


def average_pr_closing_time(
    repo,
    days=90
):
    """
    Average PR resolution time for PRs closed
    during the last N days.

    Resolution time = closed_at - created_at.
    """

    conn = get_connection()

    try:
        df = pd.read_sql(
            """
            SELECT created_at, closed_at
            FROM pull_requests
            WHERE repo = ?
            AND closed_at IS NOT NULL
            """,
            conn,
            params=(repo,)
        )
    finally:
        conn.close()

    if df.empty:
        return None

    df["created_at"] = pd.to_datetime(
        df["created_at"],
        utc=True,
        errors="coerce"
    )

    df["closed_at"] = pd.to_datetime(
        df["closed_at"],
        utc=True,
        errors="coerce"
    )

    cutoff = (
        pd.Timestamp.now(tz="UTC")
        - pd.Timedelta(days=days)
    )

    recent_closed = df[
        df["closed_at"] > cutoff
    ].copy()

    if recent_closed.empty:
        return None

    hours = (
        recent_closed["closed_at"]
        - recent_closed["created_at"]
    ).dt.total_seconds() / 3600

    hours = hours.dropna()

    if hours.empty:
        return None

    return float(
        hours.mean()
    )


def average_issue_resolution_time(
    repo,
    days=90
):
    """
    Average issue resolution time for issues closed
    during the last N days.

    Resolution time = closed_at - created_at.
    """

    conn = get_connection()

    try:
        df = pd.read_sql(
            """
            SELECT created_at, closed_at
            FROM issues
            WHERE repo = ?
            AND closed_at IS NOT NULL
            """,
            conn,
            params=(repo,)
        )
    finally:
        conn.close()

    if df.empty:
        return None

    df["created_at"] = pd.to_datetime(
        df["created_at"],
        utc=True,
        errors="coerce"
    )

    df["closed_at"] = pd.to_datetime(
        df["closed_at"],
        utc=True,
        errors="coerce"
    )

    cutoff = (
        pd.Timestamp.now(tz="UTC")
        - pd.Timedelta(days=days)
    )

    recent_closed = df[
        df["closed_at"] > cutoff
    ].copy()

    if recent_closed.empty:
        return None

    hours = (
        recent_closed["closed_at"]
        - recent_closed["created_at"]
    ).dt.total_seconds() / 3600

    hours = hours.dropna()

    if hours.empty:
        return None

    return float(
        hours.mean()
    )


def open_pull_requests(repo):
    """Return the number of currently open pull requests."""

    conn = get_connection()

    try:
        result = conn.execute(
            """
            SELECT COUNT(*)
            FROM pull_requests
            WHERE repo = ?
            AND state = 'open'
            """,
            (repo,)
        ).fetchone()[0]
    finally:
        conn.close()

    return int(result)


def open_issues(repo):
    """Return the number of currently open issues."""

    conn = get_connection()

    try:
        result = conn.execute(
            """
            SELECT COUNT(*)
            FROM issues
            WHERE repo = ?
            AND state = 'open'
            """,
            (repo,)
        ).fetchone()[0]
    finally:
        conn.close()

    return int(result)


def closed_pull_requests_last_90_days(repo):
    """Return PRs closed during the last 90 days."""

    conn = get_connection()

    try:
        df = pd.read_sql(
            """
            SELECT closed_at
            FROM pull_requests
            WHERE repo = ?
            AND closed_at IS NOT NULL
            """,
            conn,
            params=(repo,)
        )
    finally:
        conn.close()

    if df.empty:
        return 0

    df["closed_at"] = pd.to_datetime(
        df["closed_at"],
        utc=True,
        errors="coerce"
    )

    cutoff = (
        pd.Timestamp.now(tz="UTC")
        - pd.Timedelta(days=90)
    )

    return int(
        (df["closed_at"] > cutoff).sum()
    )


def closed_issues_last_90_days(repo):
    """Return issues closed during the last 90 days."""

    conn = get_connection()

    try:
        df = pd.read_sql(
            """
            SELECT closed_at
            FROM issues
            WHERE repo = ?
            AND closed_at IS NOT NULL
            """,
            conn,
            params=(repo,)
        )
    finally:
        conn.close()

    if df.empty:
        return 0

    df["closed_at"] = pd.to_datetime(
        df["closed_at"],
        utc=True,
        errors="coerce"
    )

    cutoff = (
        pd.Timestamp.now(tz="UTC")
        - pd.Timedelta(days=90)
    )

    return int(
        (df["closed_at"] > cutoff).sum()
    )