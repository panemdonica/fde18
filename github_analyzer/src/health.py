from src.metrics import (
    get_connection,
    commit_frequency,
    contributor_retention,
    average_pr_closing_time,
    average_issue_resolution_time
)


def normalize(
    value,
    reference_max
):
    """
    Scale a positive value to a number between 0 and 1.

    None means that the metric has no available data.
    """

    if value is None:
        return None

    if reference_max <= 0:
        return 0.0

    return min(
        max(value, 0) / reference_max,
        1.0
    )


def inverse_normalize(
    value,
    target
):
    """
    Convert a lower-is-better metric into a score between 0 and 1.

    None means that the metric has no available data.

    A value at or below the target receives 1.0.
    Larger values receive progressively smaller scores.
    """

    if value is None:
        return None

    if value <= 0:
        return 1.0

    if target <= 0:
        return 0.0

    return min(
        target / value,
        1.0
    )


def health_score(
    commit_freq_per_week,
    active_contributors,
    avg_pr_closing_hrs,
    avg_issue_resolution_hrs,
    weights=None
):
    """
    Calculate a Repository Health Score out of 100.

    Components:
        - Commit activity
        - Contributor activity
        - PR closing speed
        - Issue resolution speed

    Metrics with no available data are excluded from the
    calculation. The remaining weights are automatically
    normalized so that the available components still
    contribute 100% of the final score.
    """

    if weights is None:

        weights = {
            "commits": 0.25,
            "contributors": 0.25,
            "pull_requests": 0.25,
            "issues": 0.25
        }

    metric_scores = {
        "commits": normalize(
            commit_freq_per_week,
            reference_max=20
        ),

        "contributors": normalize(
            active_contributors,
            reference_max=15
        ),

        "pull_requests": inverse_normalize(
            avg_pr_closing_hrs,
            target=72
        ),

        "issues": inverse_normalize(
            avg_issue_resolution_hrs,
            target=168
        )
    }

    # --------------------------------------------------
    # KEEP ONLY METRICS WITH AVAILABLE DATA
    # --------------------------------------------------

    available_metrics = {
        name: score
        for name, score in metric_scores.items()
        if score is not None
        and weights.get(name, 0) > 0
    }

    if not available_metrics:
        return None

    # --------------------------------------------------
    # NORMALIZE AVAILABLE WEIGHTS
    # --------------------------------------------------

    available_weight = sum(
        weights[name]
        for name in available_metrics
    )

    if available_weight <= 0:
        return None

    # --------------------------------------------------
    # CALCULATE WEIGHTED SCORE
    # --------------------------------------------------

    weighted_score = sum(
        metric_scores[name]
        * weights[name]
        for name in available_metrics
    )

    score = (
        weighted_score
        / available_weight
    ) * 100

    return round(
        score,
        1
    )


def calculate_repository_health(
    repo,
    weights=None
):
    """
    Calculate the health score directly from the database.
    """

    conn = get_connection()

    try:

        frequency = commit_frequency(
            conn,
            repo
        )

        if frequency.empty:

            recent_avg_weekly_commits = None

        else:

            recent_avg_weekly_commits = float(
                frequency.tail(4).mean()
            )

        contributors = contributor_retention(
            conn,
            repo,
            days=90
        )

    finally:

        conn.close()

    pr_time = average_pr_closing_time(
        repo,
        days=90
    )

    issue_time = average_issue_resolution_time(
        repo,
        days=90
    )

    return health_score(
        commit_freq_per_week=(
            recent_avg_weekly_commits
        ),

        active_contributors=(
            contributors
        ),

        avg_pr_closing_hrs=(
            pr_time
        ),

        avg_issue_resolution_hrs=(
            issue_time
        ),

        weights=weights
    )


if __name__ == "__main__":

    repo = "react/create-react-app"

    score = calculate_repository_health(
        repo
    )

    print(
        f"{repo}"
    )

    if score is None:

        print(
            "Health Score: N/A — insufficient data"
        )

    else:

        print(
            f"Health Score: {score}/100"
        )