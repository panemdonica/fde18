import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

from src.config import BASE_URL, HEADERS


RECENT_DAYS = 90
MAX_PAGES = 3
REQUEST_TIMEOUT = 30


def get_recent_timestamp(days=RECENT_DAYS):
    """Return an ISO 8601 timestamp for the recent activity window."""

    cutoff = (
        datetime.now(timezone.utc)
        - timedelta(days=days)
    )

    return cutoff.strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def fetch_all_pages(
    url,
    params=None,
    max_pages=MAX_PAGES,
    stop_before=None,
    date_field="updated_at"
):
    """
    Fetch multiple pages from the GitHub API.

    If stop_before is provided, pagination stops once the
    returned records are older than the cutoff timestamp.
    """

    results = []
    page_count = 0

    while url and page_count < max_pages:

        print(
            f"Fetching page {page_count + 1}: {url}"
        )

        response = requests.get(
            url,
            headers=HEADERS,
            params=params,
            timeout=REQUEST_TIMEOUT
        )

        print(
            "Status Code:",
            response.status_code
        )

        if response.status_code != 200:

            print(
                "Error:",
                response.status_code,
                response.text
            )

            break

        page_data = response.json()

        if not isinstance(
            page_data,
            list
        ):
            print(
                "Unexpected API response format."
            )
            break

        results.extend(
            page_data
        )

        page_count += 1

        if stop_before and page_data:

            timestamps = []

            for item in page_data:

                value = item.get(
                    date_field
                )

                if value:
                    timestamps.append(
                        value
                    )

            if timestamps:

                oldest_timestamp = min(
                    timestamps
                )

                if oldest_timestamp < stop_before:

                    print(
                        "Reached records older "
                        "than the analysis window."
                    )

                    break

        url = (
            response.links
            .get(
                "next",
                {}
            )
            .get("url")
        )

        params = None

        time.sleep(0.2)

    print(
        f"Fetched {len(results)} records."
    )

    return results


def get_popular_repositories(
    max_results=12
):
    """Get popular public GitHub repositories."""

    url = (
        f"{BASE_URL}/search/repositories"
    )

    params = {
        "q": "stars:>1000",
        "sort": "stars",
        "order": "desc",
        "per_page": max_results
    }

    response = requests.get(
        url,
        headers=HEADERS,
        params=params,
        timeout=REQUEST_TIMEOUT
    )

    print(
        "Popular Repositories Status Code:",
        response.status_code
    )

    if response.status_code != 200:

        print(
            "Popular Repositories Error:",
            response.status_code,
            response.text
        )

        return []

    data = response.json()

    return data.get(
        "items",
        []
    )


def search_repositories(
    query,
    max_results=10
):
    """Search GitHub repositories by keyword."""

    url = (
        f"{BASE_URL}/search/repositories"
    )

    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": max_results
    }

    response = requests.get(
        url,
        headers=HEADERS,
        params=params,
        timeout=REQUEST_TIMEOUT
    )

    print(
        "Search Status Code:",
        response.status_code
    )

    if response.status_code != 200:

        print(
            "Search Error:",
            response.status_code,
            response.text
        )

        return []

    data = response.json()

    return data.get(
        "items",
        []
    )


def fetch_commits(
    owner,
    repo
):
    """Fetch commits from the recent analysis window."""

    url = (
        f"{BASE_URL}/repos/"
        f"{owner}/{repo}/commits"
    )

    since = get_recent_timestamp()

    params = {
        "since": since,
        "per_page": 100
    }

    print(
        f"Fetching commits since {since}"
    )

    return fetch_all_pages(
        url,
        params=params
    )


def fetch_pulls(
    owner,
    repo
):
    """Fetch recently updated pull requests."""

    url = (
        f"{BASE_URL}/repos/"
        f"{owner}/{repo}/pulls"
    )

    since = get_recent_timestamp()

    params = {
        "state": "all",
        "sort": "updated",
        "direction": "desc",
        "per_page": 100
    }

    print(
        f"Fetching recently updated pull requests "
        f"since {since}"
    )

    pulls = fetch_all_pages(
        url,
        params=params,
        stop_before=since,
        date_field="updated_at"
    )

    return [
        pull
        for pull in pulls
        if (
            pull.get("updated_at")
            and pull.get("updated_at") >= since
        )
    ]


def fetch_issues(
    owner,
    repo
):
    """
    Fetch recently updated issues.

    GitHub's Issues API also returns pull requests,
    so pull requests are explicitly removed.
    """

    url = (
        f"{BASE_URL}/repos/"
        f"{owner}/{repo}/issues"
    )

    since = get_recent_timestamp()

    params = {
        "state": "all",
        "sort": "updated",
        "direction": "desc",
        "since": since,
        "per_page": 100
    }

    print(
        f"Fetching issues since {since}"
    )

    issues = fetch_all_pages(
        url,
        params=params
    )

    real_issues = [
        issue
        for issue in issues
        if "pull_request" not in issue
    ]

    removed_pull_requests = (
        len(issues)
        - len(real_issues)
    )

    print(
        f"Removed {removed_pull_requests} "
        f"pull requests from issue data."
    )

    return real_issues


def save_raw(
    data,
    name
):
    """Save API data as a timestamped JSON file."""

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    project_root = (
        Path(__file__)
        .resolve()
        .parent
        .parent
    )

    raw_dir = (
        project_root
        / "data"
        / "raw"
    )

    raw_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    path = (
        raw_dir
        / f"{name}_{timestamp}.json"
    )

    with open(
        path,
        "w"
    ) as file:

        json.dump(
            data,
            file,
            indent=2
        )

    print(
        f"Saved {len(data)} records to {path}"
    )


def analyze_repository(
    owner,
    repo
):
    """Fetch and save recent GitHub data for a repository."""

    print(
        f"\nStarting analysis for "
        f"{owner}/{repo}"
    )

    print(
        "\nFetching recent commits..."
    )

    commits = fetch_commits(
        owner,
        repo
    )

    save_raw(
        commits,
        f"{owner}_{repo}_commits"
    )

    print(
        "\nFetching recent pull requests..."
    )

    pulls = fetch_pulls(
        owner,
        repo
    )

    save_raw(
        pulls,
        f"{owner}_{repo}_pulls"
    )

    print(
        "\nFetching recent issues..."
    )

    issues = fetch_issues(
        owner,
        repo
    )

    save_raw(
        issues,
        f"{owner}_{repo}_issues"
    )

    print(
        f"\nAnalysis completed for "
        f"{owner}/{repo}"
    )

    print(
        "\nRecords collected:"
    )

    print(
        f"  Commits: {len(commits)}"
    )

    print(
        f"  Pull Requests: {len(pulls)}"
    )

    print(
        f"  Issues: {len(issues)}"
    )

    return {
        "commits": commits,
        "pulls": pulls,
        "issues": issues
    }