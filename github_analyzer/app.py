import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.ingest import (
    search_repositories,
    get_popular_repositories,
    analyze_repository
)

from src.load import (
    load_repository_data
)

from src.metrics import (
    get_connection,
    commit_frequency,
    active_contributors,
    average_pr_closing_time,
    average_issue_resolution_time,
    open_pull_requests,
    open_issues,
    closed_pull_requests_last_90_days,
    closed_issues_last_90_days
)

from src.health import (
    health_score
)


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

DB_PATH = "data/gitpulse.db"

st.set_page_config(
    page_title="GitPulse",
    page_icon="📊",
    layout="wide"
)

st.title(
    "📊 GitPulse — GitHub Developer Analytics"
)

st.write(
    "Search, discover, and analyze public GitHub repositories "
    "using developer activity, pull requests, issues, and "
    "repository health metrics."
)


# --------------------------------------------------
# DATABASE FUNCTIONS
# --------------------------------------------------

@st.cache_data(ttl=300)
def load_table(table_name):
    """Load a table from the SQLite database."""

    if not Path(DB_PATH).exists():
        return pd.DataFrame()

    conn = sqlite3.connect(DB_PATH)

    try:
        df = pd.read_sql(
            f"SELECT * FROM {table_name}",
            conn
        )
    finally:
        conn.close()

    return df


# --------------------------------------------------
# POPULAR REPOSITORIES
# --------------------------------------------------

@st.cache_data(ttl=600)
def load_popular_repositories():
    """Load popular repositories from GitHub."""

    return get_popular_repositories(
        max_results=12
    )


# --------------------------------------------------
# REPOSITORY DISCOVERY
# --------------------------------------------------

st.header(
    "🔎 Repository Discovery"
)

st.write(
    "Search for a specific GitHub repository or explore "
    "popular repositories to begin your analysis."
)


# --------------------------------------------------
# SEARCH BAR
# --------------------------------------------------

search_col, button_col = st.columns(
    [5, 1]
)

with search_col:

    search_query = st.text_input(
        "Search GitHub repositories",
        placeholder=(
            "e.g. react, tensorflow, kubernetes"
        ),
        label_visibility="collapsed"
    )

with button_col:

    search_button = st.button(
        "🔍 Search",
        use_container_width=True
    )


# --------------------------------------------------
# PERFORM SEARCH
# --------------------------------------------------

if search_button:

    if not search_query.strip():

        st.warning(
            "Please enter a repository name or topic."
        )

    else:

        with st.spinner(
            "Searching GitHub..."
        ):

            results = search_repositories(
                search_query.strip()
            )

        st.session_state[
            "search_results"
        ] = results

        st.session_state.pop(
            "selected_repository",
            None
        )

        st.session_state.pop(
            "selected_repo_data",
            None
        )

        st.session_state.pop(
            "analysis_complete",
            None
        )


# --------------------------------------------------
# DETERMINE WHAT TO DISPLAY
# --------------------------------------------------

search_results = st.session_state.get(
    "search_results",
    []
)

if search_results:

    st.subheader(
        f'🔎 Search Results for "{search_query}"'
    )

    repositories_to_display = (
        search_results
    )

else:

    st.subheader(
        "🌟 Popular Repositories"
    )

    with st.spinner(
        "Loading popular repositories..."
    ):

        repositories_to_display = (
            load_popular_repositories()
        )


# --------------------------------------------------
# REPOSITORY CARDS
# --------------------------------------------------

for start in range(
    0,
    len(repositories_to_display),
    3
):

    row = repositories_to_display[
        start:start + 3
    ]

    columns = st.columns(3)

    for column, repository in zip(
        columns,
        row
    ):

        with column:

            st.markdown(
                f"### {repository['full_name']}"
            )

            description = (
                repository.get(
                    "description"
                )
                or "No description available."
            )

            if len(description) > 150:

                description = (
                    description[:150]
                    + "..."
                )

            st.write(
                description
            )

            metric_col1, metric_col2 = (
                st.columns(2)
            )

            metric_col1.metric(
                "⭐ Stars",
                f"{repository['stargazers_count']:,}"
            )

            metric_col2.metric(
                "🍴 Forks",
                f"{repository['forks_count']:,}"
            )

            language = (
                repository.get(
                    "language"
                )
                or "Unknown"
            )

            st.caption(
                f"💻 {language}"
            )

            if st.button(
                "Select Repository",
                key=(
                    f"select_"
                    f"{repository['id']}"
                ),
                use_container_width=True
            ):

                st.session_state[
                    "selected_repository"
                ] = repository[
                    "full_name"
                ]

                st.session_state[
                    "selected_repo_data"
                ] = repository

                st.session_state.pop(
                    "analysis_complete",
                    None
                )

                st.rerun()

    st.markdown("---")


# --------------------------------------------------
# SELECTED REPOSITORY
# --------------------------------------------------

selected_repository = (
    st.session_state.get(
        "selected_repository"
    )
)

if not selected_repository:

    st.info(
        "Select a repository above to continue."
    )

    st.stop()


selected_repo_data = (
    st.session_state[
        "selected_repo_data"
    ]
)


st.header(
    f"📦 Selected Repository — "
    f"{selected_repository}"
)


col1, col2, col3, col4 = st.columns(4)


col1.metric(
    "⭐ Stars",
    f"{selected_repo_data['stargazers_count']:,}"
)


col2.metric(
    "🍴 Forks",
    f"{selected_repo_data['forks_count']:,}"
)


col3.metric(
    "🐛 Open Issues",
    f"{selected_repo_data['open_issues_count']:,}"
)


col4.metric(
    "💻 Language",
    selected_repo_data.get(
        "language"
    ) or "Unknown"
)


st.write(
    selected_repo_data.get(
        "description",
        "No description available."
    )
)


# --------------------------------------------------
# ANALYSIS METHODOLOGY
# --------------------------------------------------

with st.expander(
    "📘 What does this repository analysis consist of?",
    expanded=True
):

    st.markdown(
        """
        ### What GitPulse analyzes

        GitPulse analyzes a GitHub repository to understand
        its recent development activity, collaboration,
        pull requests, and issues.

        **1. Commits**

        Tracks recent code changes and shows how frequently
        developers are committing to the repository.

        **2. Contributors**

        Measures how many unique contributors have been
        active recently based on their commit activity.

        **3. Pull Requests**

        Analyzes pull request activity, including open PRs,
        recently closed PRs, and the time taken to close them.

        **4. Issues**

        Analyzes open and recently closed issues, including
        how long closed issues took to be resolved.

        **5. Repository Health**

        Combines development and collaboration metrics into
        a normalized Health Score from 0–100.

        ### How the Health Score is calculated

        Each metric is first converted into a score from
        **0–100**.

        - **Commit Frequency:** higher weekly activity produces a higher score.
        - **Active Contributors:** more active contributors produces a higher score.
        - **PR Closing Speed:** faster PR closure produces a higher score.
        - **Issue Resolution Speed:** faster issue resolution produces a higher score.

        The individual scores are then combined using the
        configured weights.

        With the default weights:

        **Health Score =**

        **25% × Commit Frequency Score**  
        **+ 25% × Contributor Score**  
        **+ 25% × PR Closing Speed Score**  
        **+ 25% × Issue Resolution Score**

        GitPulse automatically normalizes the available weights
        when a metric does not have sufficient data.

        ### Health Score reference targets

        GitPulse currently uses these reference values:

        - **Commit Frequency:** 20 commits/week
        - **Active Contributors:** 15 contributors
        - **PR Closing Time:** 72 hours
        - **Issue Resolution Time:** 168 hours

        For activity metrics, reaching the reference value corresponds
        to a score of 100.

        For time-based metrics, reaching or beating the target corresponds
        to a score of 100.

        ### How the analysis works

        GitPulse follows a data pipeline:

        **GitHub API**
        → **Data Ingestion**
        → **Raw JSON**
        → **Transformation**
        → **SQLite Database**
        → **Metrics**
        → **Health Score**
        → **Dashboard**

        ### Analysis windows

        - **Commits:** recent 30-day activity
        - **Contributors:** activity during the last 90 days
        - **Pull Requests:** recently updated PRs within the analysis window
        - **Issues:** recently updated issues within the analysis window
        - **PR/Issue resolution:** items closed during the recent 90-day period

        **Important:** A PR or issue can have been created years ago
        but closed recently. In that case, GitPulse measures the
        full time between its original creation and closure.
        """
    )


st.info(
    f"Selected repository: "
    f"**{selected_repository}**"
)


# --------------------------------------------------
# ANALYZE SELECTED REPOSITORY
# --------------------------------------------------

st.markdown("---")

st.subheader(
    "🚀 Repository Analysis"
)

st.write(
    "Fetch commits, pull requests, and issues from "
    "GitHub, transform the data, and load it into "
    "the GitPulse analytics database."
)


analyze_button = st.button(
    "🚀 Analyze Repository",
    use_container_width=True,
    type="primary"
)


if analyze_button:

    owner, repository_name = (
        selected_repository.split(
            "/",
            1
        )
    )

    try:

        with st.spinner(
            f"Fetching GitHub data for "
            f"{selected_repository}..."
        ):

            analysis_data = (
                analyze_repository(
                    owner,
                    repository_name
                )
            )

        with st.spinner(
            "Transforming data and loading "
            "the GitPulse database..."
        ):

            load_counts = (
                load_repository_data(
                    commits=analysis_data[
                        "commits"
                    ],
                    pulls=analysis_data[
                        "pulls"
                    ],
                    issues=analysis_data[
                        "issues"
                    ],
                    repo=selected_repository
                )
            )

        load_table.clear()

        st.session_state[
            "analysis_complete"
        ] = True

        st.session_state[
            "analysis_counts"
        ] = {
            "commits": load_counts[
                "commits"
            ],
            "pulls": load_counts[
                "pulls"
            ],
            "issues": load_counts[
                "issues"
            ]
        }

        st.success(
            f"**{selected_repository}** "
            "has been successfully analyzed."
        )

        st.rerun()

    except Exception as error:

        st.error(
            "Repository analysis failed."
        )

        st.exception(
            error
        )

        st.stop()


# --------------------------------------------------
# LOAD DATABASE DATA AFTER ANALYSIS
# --------------------------------------------------

commits = load_table(
    "commits"
)

prs = load_table(
    "pull_requests"
)

issues = load_table(
    "issues"
)


# --------------------------------------------------
# ANALYSIS STATUS
# --------------------------------------------------

if st.session_state.get(
    "analysis_complete",
    False
):

    counts = st.session_state[
        "analysis_counts"
    ]

    st.success(
        f"Database updated — "
        f"{counts['commits']:,} commits, "
        f"{counts['pulls']:,} pull requests, "
        f"{counts['issues']:,} issues."
    )


# --------------------------------------------------
# HEALTH SCORE SETTINGS
# --------------------------------------------------

st.sidebar.markdown("---")

st.sidebar.subheader(
    "Health Score Settings"
)

st.sidebar.caption(
    "The Health Score is calculated centrally by "
    "src/health.py using the configured metric weights."
)


w_commits = st.sidebar.slider(
    "Commit Frequency Weight",
    min_value=0.0,
    max_value=1.0,
    value=0.25,
    step=0.05
)


w_contributors = st.sidebar.slider(
    "Contributor Weight",
    min_value=0.0,
    max_value=1.0,
    value=0.25,
    step=0.05
)


w_pr = st.sidebar.slider(
    "PR Closing Speed Weight",
    min_value=0.0,
    max_value=1.0,
    value=0.25,
    step=0.05
)


w_issues = st.sidebar.slider(
    "Issue Resolution Weight",
    min_value=0.0,
    max_value=1.0,
    value=0.25,
    step=0.05
)


weights = {
    "commits": w_commits,
    "contributors": w_contributors,
    "pull_requests": w_pr,
    "issues": w_issues
}


# --------------------------------------------------
# HEALTH SCORE METHODOLOGY
# --------------------------------------------------

with st.sidebar.expander(
    "📐 Health Score Methodology",
    expanded=False
):

    st.markdown(
        """
        ### How your score is calculated

        GitPulse calculates a **0–100 Repository Health Score**
        from four components:

        **1. Commit Frequency**

        Measures recent development activity.

        Reference: **20 commits/week**

        **2. Active Contributors**

        Measures the number of contributors active during
        the last 90 days.

        Reference: **15 contributors**

        **3. PR Closing Speed**

        Measures how quickly pull requests are closed.

        Target: **72 hours**

        Faster closure produces a higher score.

        **4. Issue Resolution Speed**

        Measures how quickly issues are resolved.

        Target: **168 hours (7 days)**

        Faster resolution produces a higher score.

        ---

        ### Default weights

        | Component | Weight |
        |---|---:|
        | Commit Frequency | 25% |
        | Active Contributors | 25% |
        | PR Closing Speed | 25% |
        | Issue Resolution Speed | 25% |

        The weights can be adjusted above.

        If a metric has no available data, GitPulse excludes
        that metric and automatically normalizes the remaining
        weights.

        ---

        ### Important

        - More commits → higher score
        - More contributors → higher score
        - Faster PR closure → higher score
        - Faster issue resolution → higher score

        The final Health Score is a composite indicator and
        should be interpreted together with the underlying
        metrics and charts.
        """
    )


# --------------------------------------------------
# FILTER DATA FOR SELECTED REPOSITORY
# --------------------------------------------------

repo = selected_repository


repo_commits = commits[
    commits["repo"] == repo
].copy()


repo_prs = prs[
    prs["repo"] == repo
].copy()


repo_issues = issues[
    issues["repo"] == repo
].copy()


# --------------------------------------------------
# CHECK IF REPOSITORY HAS BEEN ANALYZED
# --------------------------------------------------

if (
    repo_commits.empty
    and repo_prs.empty
    and repo_issues.empty
):

    st.markdown("---")

    st.warning(
        f"**{repo}** has not been analyzed yet."
    )

    st.info(
        "Click **🚀 Analyze Repository** above "
        "to collect and process its GitHub data."
    )

    st.stop()


# --------------------------------------------------
# CENTRALIZED METRICS
# --------------------------------------------------

try:

    conn = get_connection()

    weekly_commit_series = (
        commit_frequency(
            conn,
            repo
        )
    )

    conn.close()

except Exception as error:

    st.error(
        "Unable to calculate repository metrics."
    )

    st.exception(
        error
    )

    st.stop()


# --------------------------------------------------
# COMMIT FREQUENCY
# --------------------------------------------------

if (
    weekly_commit_series is not None
    and hasattr(
        weekly_commit_series,
        "tail"
    )
):

    recent_weekly_commits = (
        weekly_commit_series
        .tail(4)
    )

    if len(recent_weekly_commits) > 0:

        commit_frequency_per_week = (
            float(
                recent_weekly_commits.mean()
            )
        )

    else:

        commit_frequency_per_week = None

else:

    commit_frequency_per_week = None


# --------------------------------------------------
# RECENT COMMITS
# --------------------------------------------------

repo_commits["date"] = pd.to_datetime(
    repo_commits["date"],
    utc=True,
    errors="coerce"
)

repo_commits = repo_commits.dropna(
    subset=["date"]
)


current_time = pd.Timestamp.now(
    tz="UTC"
)

thirty_days_ago = (
    current_time
    - pd.Timedelta(
        days=30
    )
)


commits_last_30_days = len(
    repo_commits[
        repo_commits["date"]
        > thirty_days_ago
    ]
)


# --------------------------------------------------
# CENTRALIZED CONTRIBUTOR METRIC
# --------------------------------------------------

try:

    active_contributor_count = (
        active_contributors(
            repo,
            days=90
        )
    )

except Exception:

    active_contributor_count = None


# --------------------------------------------------
# CENTRALIZED PR METRIC
# --------------------------------------------------

try:

    avg_pr_time = (
        average_pr_closing_time(
            repo,
            days=90
        )
    )

except Exception:

    avg_pr_time = None


# --------------------------------------------------
# CENTRALIZED ISSUE METRIC
# --------------------------------------------------

try:

    avg_issue_time = (
        average_issue_resolution_time(
            repo,
            days=90
        )
    )

except Exception:

    avg_issue_time = None


# --------------------------------------------------
# CENTRALIZED PR / ISSUE COUNTS
# --------------------------------------------------

try:

    open_pr_count = (
        open_pull_requests(
            repo
        )
    )

except Exception:

    open_pr_count = 0


try:

    open_issue_count = (
        open_issues(
            repo
        )
    )

except Exception:

    open_issue_count = 0


try:

    closed_pr_count = (
        closed_pull_requests_last_90_days(
            repo
        )
    )

except Exception:

    closed_pr_count = 0


try:

    closed_issue_count = (
        closed_issues_last_90_days(
            repo
        )
    )

except Exception:

    closed_issue_count = 0


# --------------------------------------------------
# HEALTH SCORE
# --------------------------------------------------

health_score_value = health_score(
    commit_freq_per_week=(
        commit_frequency_per_week
    ),
    active_contributors=(
        active_contributor_count
    ),
    avg_pr_closing_hrs=(
        avg_pr_time
    ),
    avg_issue_resolution_hrs=(
        avg_issue_time
    ),
    weights=weights
)


# --------------------------------------------------
# INDIVIDUAL HEALTH COMPONENT SCORES
# --------------------------------------------------

commit_component = health_score(
    commit_freq_per_week=(
        commit_frequency_per_week
    ),
    active_contributors=(
        active_contributor_count
    ),
    avg_pr_closing_hrs=(
        avg_pr_time
    ),
    avg_issue_resolution_hrs=(
        avg_issue_time
    ),
    weights={
        "commits": 1.0,
        "contributors": 0.0,
        "pull_requests": 0.0,
        "issues": 0.0
    }
)


contributor_component = health_score(
    commit_freq_per_week=(
        commit_frequency_per_week
    ),
    active_contributors=(
        active_contributor_count
    ),
    avg_pr_closing_hrs=(
        avg_pr_time
    ),
    avg_issue_resolution_hrs=(
        avg_issue_time
    ),
    weights={
        "commits": 0.0,
        "contributors": 1.0,
        "pull_requests": 0.0,
        "issues": 0.0
    }
)


pr_component = health_score(
    commit_freq_per_week=(
        commit_frequency_per_week
    ),
    active_contributors=(
        active_contributor_count
    ),
    avg_pr_closing_hrs=(
        avg_pr_time
    ),
    avg_issue_resolution_hrs=(
        avg_issue_time
    ),
    weights={
        "commits": 0.0,
        "contributors": 0.0,
        "pull_requests": 1.0,
        "issues": 0.0
    }
)


issue_component = health_score(
    commit_freq_per_week=(
        commit_frequency_per_week
    ),
    active_contributors=(
        active_contributor_count
    ),
    avg_pr_closing_hrs=(
        avg_pr_time
    ),
    avg_issue_resolution_hrs=(
        avg_issue_time
    ),
    weights={
        "commits": 0.0,
        "contributors": 0.0,
        "pull_requests": 0.0,
        "issues": 1.0
    }
)


# --------------------------------------------------
# DASHBOARD METRICS
# --------------------------------------------------

st.markdown("---")

st.subheader(
    f"📈 Repository Overview — {repo}"
)


col1, col2, col3, col4 = st.columns(4)


if health_score_value is not None:

    col1.metric(
        "Repository Health Score",
        f"{health_score_value:.1f}/100"
    )

else:

    col1.metric(
        "Repository Health Score",
        "N/A"
    )


col2.metric(
    "Commits (Last 30 Days)",
    commits_last_30_days
)


if active_contributor_count is not None:

    col3.metric(
        "Active Contributors (90 Days)",
        active_contributor_count
    )

else:

    col3.metric(
        "Active Contributors (90 Days)",
        "N/A"
    )


if avg_pr_time is not None:

    col4.metric(
        "Average PR Closing Time",
        f"{avg_pr_time:.1f} hrs"
    )

else:

    col4.metric(
        "Average PR Closing Time",
        "N/A"
    )


# --------------------------------------------------
# HEALTH SCORE BREAKDOWN
# --------------------------------------------------

st.markdown("---")

st.subheader(
    "Health Score Breakdown"
)


score_data = pd.DataFrame({
    "Metric": [
        "Commit Frequency",
        "Active Contributors",
        "PR Closing Speed",
        "Issue Resolution Speed"
    ],

    "Score": [
        commit_component,
        contributor_component,
        pr_component,
        issue_component
    ]
})


score_data = score_data.dropna(
    subset=["Score"]
)


if not score_data.empty:

    health_chart = px.bar(
        score_data,
        x="Metric",
        y="Score",
        range_y=[0, 100],
        title="Individual Metric Scores"
    )

    st.plotly_chart(
        health_chart,
        use_container_width=True
    )

else:

    st.info(
        "Not enough data to calculate the Health Score."
    )


# --------------------------------------------------
# COMMIT FREQUENCY CHART
# --------------------------------------------------

st.markdown("---")

st.subheader(
    f"📅 Weekly Commit Frequency — {repo}"
)


if not repo_commits.empty:

    repo_commits["week"] = (
        repo_commits["date"]
        .dt.tz_localize(None)
        .dt.to_period("W")
        .dt.start_time
    )

    commit_frequency_chart_data = (
        repo_commits
        .groupby("week")
        .size()
        .reset_index(
            name="commits"
        )
    )

    if not commit_frequency_chart_data.empty:

        commit_chart = px.line(
            commit_frequency_chart_data,
            x="week",
            y="commits",
            markers=True,
            title="Commits Per Week"
        )

        st.plotly_chart(
            commit_chart,
            use_container_width=True
        )

    else:

        st.info(
            "No commit data available."
        )

else:

    st.info(
        "No commit data available."
    )


# --------------------------------------------------
# PR DISTRIBUTION
# --------------------------------------------------

st.markdown("---")

st.subheader(
    "🔀 Pull Request Closing Time Distribution"
)


closed_prs = pd.DataFrame()

if not repo_prs.empty:

    repo_prs["created_at"] = pd.to_datetime(
        repo_prs["created_at"],
        utc=True,
        errors="coerce"
    )

    repo_prs["closed_at"] = pd.to_datetime(
        repo_prs["closed_at"],
        utc=True,
        errors="coerce"
    )

    closed_prs = repo_prs.dropna(
        subset=[
            "created_at",
            "closed_at"
        ]
    ).copy()

    if not closed_prs.empty:

        closed_prs[
            "resolution_hours"
        ] = (
            closed_prs["closed_at"]
            - closed_prs["created_at"]
        ).dt.total_seconds() / 3600


if not closed_prs.empty:

    pr_chart = px.histogram(
        closed_prs,
        x="resolution_hours",
        nbins=30,
        title=(
            "Pull Request Closing Time "
            "(Hours)"
        )
    )

    st.plotly_chart(
        pr_chart,
        use_container_width=True
    )

else:

    st.info(
        "No closed pull requests available."
    )


# --------------------------------------------------
# ISSUE DISTRIBUTION
# --------------------------------------------------

st.markdown("---")

st.subheader(
    "🐛 Issue Resolution Time Distribution"
)


closed_issues = pd.DataFrame()

if not repo_issues.empty:

    repo_issues["created_at"] = pd.to_datetime(
        repo_issues["created_at"],
        utc=True,
        errors="coerce"
    )

    repo_issues["closed_at"] = pd.to_datetime(
        repo_issues["closed_at"],
        utc=True,
        errors="coerce"
    )

    closed_issues = repo_issues.dropna(
        subset=[
            "created_at",
            "closed_at"
        ]
    ).copy()

    if not closed_issues.empty:

        closed_issues[
            "resolution_hours"
        ] = (
            closed_issues["closed_at"]
            - closed_issues["created_at"]
        ).dt.total_seconds() / 3600


if not closed_issues.empty:

    issue_chart = px.histogram(
        closed_issues,
        x="resolution_hours",
        nbins=30,
        title=(
            "Issue Resolution Time "
            "(Hours)"
        )
    )

    st.plotly_chart(
        issue_chart,
        use_container_width=True
    )

else:

    st.info(
        "No closed issues available."
    )


# --------------------------------------------------
# ISSUE METRICS
# --------------------------------------------------

st.markdown("---")

st.subheader(
    "🐛 Issue Statistics"
)


issue_col1, issue_col2, issue_col3 = (
    st.columns(3)
)


total_issues = (
    closed_issue_count
    + open_issue_count
)


issue_col1.metric(
    "Total Issues",
    total_issues
)


issue_col2.metric(
    "Closed Issues (90 Days)",
    closed_issue_count
)


issue_col3.metric(
    "Open Issues",
    open_issue_count
)


# --------------------------------------------------
# PR METRICS
# --------------------------------------------------

st.markdown("---")

st.subheader(
    "🔀 Pull Request Statistics"
)


pr_col1, pr_col2, pr_col3 = (
    st.columns(3)
)


pr_col1.metric(
    "Open Pull Requests",
    open_pr_count
)


pr_col2.metric(
    "Closed PRs (90 Days)",
    closed_pr_count
)


if avg_pr_time is not None:

    pr_col3.metric(
        "Average Closing Time",
        f"{avg_pr_time:.1f} hrs"
    )

else:

    pr_col3.metric(
        "Average Closing Time",
        "N/A"
    )


# --------------------------------------------------
# AVERAGE ISSUE RESOLUTION TIME
# --------------------------------------------------

if avg_issue_time is not None:

    st.write(
        f"**Average Issue Resolution Time:** "
        f"{avg_issue_time:.1f} hours"
    )

else:

    st.write(
        "**Average Issue Resolution Time:** N/A"
    )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.markdown("---")

st.caption(
    "GitPulse — GitHub Developer Analytics Pipeline"
)