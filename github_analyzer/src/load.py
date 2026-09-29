import sqlite3
from pathlib import Path

from src.transform import (
    transform_repository_data
)


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

SCHEMA_PATH = (
    PROJECT_ROOT
    / "schema.sql"
)


def get_connection():
    """Create a connection to the SQLite database."""

    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    conn = sqlite3.connect(
        DB_PATH
    )

    with open(
        SCHEMA_PATH,
        "r"
    ) as file:

        conn.executescript(
            file.read()
        )

    return conn


def delete_repository_data(
    repo,
    conn
):
    """
    Remove existing data for the repository
    before loading its refreshed analysis.
    """

    tables = [
        "commits",
        "pull_requests",
        "issues"
    ]

    for table in tables:

        cursor = conn.execute(
            f"DELETE FROM {table} "
            f"WHERE repo = ?",
            (repo,)
        )

        print(
            f"Removed {cursor.rowcount} old rows "
            f"from {table} for {repo}"
        )


def load_dataframe(
    df,
    table_name,
    conn
):
    """Insert transformed data into SQLite."""

    if df.empty:

        print(
            f"No records to load into {table_name}."
        )

        return

    df.to_sql(
        table_name,
        conn,
        if_exists="append",
        index=False
    )

    print(
        f"Inserted {len(df)} rows "
        f"into {table_name}"
    )


def load_repository_data(
    commits,
    pulls,
    issues,
    repo
):
    """
    Refresh and load all data for a repository.
    """

    print(
        f"\nLoading data for {repo}..."
    )

    transformed = transform_repository_data(
        commits,
        pulls,
        issues,
        repo
    )

    commits_df = transformed[
        "commits"
    ]

    pulls_df = transformed[
        "pulls"
    ]

    issues_df = transformed[
        "issues"
    ]

    conn = get_connection()

    try:

        # Remove only this repository's old data.
        delete_repository_data(
            repo,
            conn
        )

        # Load refreshed data.
        load_dataframe(
            commits_df,
            "commits",
            conn
        )

        load_dataframe(
            pulls_df,
            "pull_requests",
            conn
        )

        load_dataframe(
            issues_df,
            "issues",
            conn
        )

        conn.commit()

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()

    print(
        f"\nDatabase refresh complete for {repo}."
    )

    return {
        "commits": len(commits_df),
        "pulls": len(pulls_df),
        "issues": len(issues_df)
    }