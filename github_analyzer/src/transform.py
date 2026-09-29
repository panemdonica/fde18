import json

import pandas as pd


def load_json_file(filepath):
    """Load and return data from a JSON file."""

    with open(
        filepath,
        "r"
    ) as file:

        data = json.load(file)

    return data


def transform_commits(commits, repo):
    """Transform raw commit data into a clean DataFrame."""

    cleaned_data = []

    for commit in commits:

        cleaned_data.append({

            "sha": commit.get("sha"),

            "repo": repo,

            "author": (
                commit
                .get("commit", {})
                .get("author", {})
                .get("name")
            ),

            "date": (
                commit
                .get("commit", {})
                .get("author", {})
                .get("date")
            ),

            "message": (
                commit
                .get("commit", {})
                .get("message")
            )

        })

    return pd.DataFrame(
        cleaned_data
    )


def transform_pulls(pulls, repo):
    """Transform raw pull request data into a clean DataFrame."""

    cleaned_data = []

    for pull in pulls:

        cleaned_data.append({

            "id": pull.get("id"),

            "repo": repo,

            "number": pull.get("number"),

            "title": pull.get("title"),

            "state": pull.get("state"),

            "created_at": pull.get("created_at"),

            "closed_at": pull.get("closed_at"),

            "author": (
                pull
                .get("user", {})
                .get("login")
            )

        })

    return pd.DataFrame(
        cleaned_data
    )


def transform_issues(issues, repo):
    """Transform raw issue data into a clean DataFrame."""

    cleaned_data = []

    for issue in issues:

        cleaned_data.append({

            "id": issue.get("id"),

            "repo": repo,

            "number": issue.get("number"),

            "title": issue.get("title"),

            "state": issue.get("state"),

            "created_at": issue.get("created_at"),

            "closed_at": issue.get("closed_at"),

            "author": (
                issue
                .get("user", {})
                .get("login")
            ),

            "comments": issue.get("comments")

        })

    return pd.DataFrame(
        cleaned_data
    )


def transform_repository_data(
    commits,
    pulls,
    issues,
    repo
):
    """
    Transform all raw GitHub data for a repository.

    Returns:
        Dictionary containing transformed DataFrames.
    """

    commits_df = transform_commits(
        commits,
        repo
    )

    pulls_df = transform_pulls(
        pulls,
        repo
    )

    issues_df = transform_issues(
        issues,
        repo
    )

    return {
        "commits": commits_df,
        "pulls": pulls_df,
        "issues": issues_df
    }