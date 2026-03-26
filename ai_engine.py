"""
ai_engine.py — Claude-powered GenAI features for the PM Dashboard.
Provides: Project Pulse, Smart Risk Advisor, and Natural Language Search.
"""

import json
import streamlit as st
import pandas as pd

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


def _get_client():
    """Get or create an Anthropic client using the API key from session."""
    api_key = st.session_state.get("anthropic_api_key", "")
    if not api_key:
        return None
    if not HAS_ANTHROPIC:
        return None
    return anthropic.Anthropic(api_key=api_key)


def _call_claude(system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
    """Make a single Claude API call and return the text response."""
    client = _get_client()
    if client is None:
        return ""
    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return message.content[0].text
    except Exception as e:
        return f"⚠️ AI Error: {str(e)}"


# ═══════════════════════════════════════════════════════════════════════════════
#  1. PROJECT PULSE — Executive summary of portfolio health
# ═══════════════════════════════════════════════════════════════════════════════

PULSE_SYSTEM = """You are a senior program management analyst for an enterprise SaaS implementation team.
You will receive a JSON summary of the current project portfolio. Analyze it and respond with EXACTLY this format:

## Overall Health: [🟢 On Track / 🟡 At Risk / 🔴 Off Track]

[3-sentence executive summary of overall implementation health. Mention specific numbers.
Highlight the most critical risks and wins. Be concise and data-driven.]

### Key Metrics
- **Projects On Track:** [count]
- **Projects At Risk:** [count with names]
- **Critical Bugs (P1):** [count]
- **Overdue Milestones:** [count]

### Top 3 Action Items
1. [Most urgent action]
2. [Second action]
3. [Third action]

Do NOT use generic language. Reference specific project names, customer names, and numbers from the data."""


def generate_project_pulse(projects_df: pd.DataFrame,
                           bugs_df: pd.DataFrame,
                           milestones_df: pd.DataFrame) -> str:
    """Generate an AI-driven executive summary of portfolio health."""
    # Build a compact data summary for the prompt
    summary = {}

    if not projects_df.empty:
        summary["total_projects"] = len(projects_df)
        if "Project Stage" in projects_df.columns:
            summary["stages"] = projects_df["Project Stage"].value_counts().to_dict()
        if "Burned %" in projects_df.columns:
            high_burn = projects_df[projects_df["Burned %"] > 90]
            summary["high_burn_projects"] = high_burn["Project Name"].tolist()[:10]
        if "% Complete" in projects_df.columns:
            summary["avg_completion"] = round(projects_df["% Complete"].mean(), 1)
            low_progress = projects_df[projects_df["% Complete"] < 20]
            summary["low_progress_projects"] = low_progress[["Project Name", "Customer Name", "% Complete"]].head(5).to_dict("records")
        if "Project Region" in projects_df.columns:
            summary["regions"] = projects_df["Project Region"].value_counts().to_dict()

    if not bugs_df.empty:
        summary["total_bugs"] = len(bugs_df)
        if "Priority" in bugs_df.columns:
            summary["bug_priorities"] = bugs_df["Priority"].value_counts().to_dict()
        if "Status" in bugs_df.columns:
            summary["bug_statuses"] = bugs_df["Status"].value_counts().to_dict()
        if "SLA Due date" in bugs_df.columns:
            overdue = bugs_df[bugs_df["SLA Due date"] < pd.Timestamp.now()]
            summary["overdue_bugs"] = len(overdue)

    if not milestones_df.empty:
        summary["total_milestones"] = len(milestones_df)
        if "Status" in milestones_df.columns:
            summary["milestone_statuses"] = milestones_df["Status"].value_counts().to_dict()
        if "Due date" in milestones_df.columns:
            overdue_ms = milestones_df[milestones_df["Due date"] < pd.Timestamp.now()]
            summary["overdue_milestones"] = len(overdue_ms)
            upcoming = milestones_df[
                (milestones_df["Due date"] >= pd.Timestamp.now()) &
                (milestones_df["Due date"] <= pd.Timestamp.now() + pd.Timedelta(days=30))
            ]
            summary["milestones_next_30_days"] = len(upcoming)

    user_prompt = f"Here is the current portfolio data summary:\n\n```json\n{json.dumps(summary, default=str, indent=2)}\n```\n\nGenerate the Project Pulse executive summary."
    return _call_claude(PULSE_SYSTEM, user_prompt, max_tokens=800)


# ═══════════════════════════════════════════════════════════════════════════════
#  2. SMART RISK ADVISOR — Per-project risk analysis
# ═══════════════════════════════════════════════════════════════════════════════

RISK_SYSTEM = """You are a risk management advisor for enterprise software implementations.
You will receive data about a specific project including its status, bugs, and milestones.

Analyze the data and respond in EXACTLY this format:

## Risk Assessment: [🟢 Low / 🟡 Medium / 🔴 High]

### Identified Risks
[List 2-4 specific risks based on the data. Each risk should reference actual data points.]

### Mitigation Recommendations
[For each risk, provide a specific, actionable mitigation step.]

### Timeline Impact
[Brief assessment of whether this project is on track for its milestones.]

Be specific. Reference actual bug counts, SLA dates, burned hours, and milestone dates from the data."""


def generate_risk_assessment(project_name: str,
                             projects_df: pd.DataFrame,
                             bugs_df: pd.DataFrame,
                             milestones_df: pd.DataFrame) -> str:
    """Generate risk analysis for a specific project."""
    project_data = {}

    # Project info
    if not projects_df.empty:
        proj_rows = projects_df[projects_df["Project Name"] == project_name]
        if not proj_rows.empty:
            row = proj_rows.iloc[0]
            project_data["project"] = {
                "name": project_name,
                "customer": row.get("Customer Name", ""),
                "stage": row.get("Project Stage", ""),
                "region": row.get("Project Region", ""),
                "pm": row.get("Project Manager", ""),
                "planned_hours": row.get("Planned Hours", 0),
                "worked_hours": row.get("Worked Hours", 0),
                "burned_pct": row.get("Burned %", 0),
                "pct_complete": row.get("% Complete", 0),
                "billing_type": row.get("Billing Type", ""),
            }

    # Bugs for this project
    if not bugs_df.empty and "Project Name" in bugs_df.columns:
        proj_bugs = bugs_df[bugs_df["Project Name"].str.contains(project_name, case=False, na=False)]
        if not proj_bugs.empty:
            project_data["bugs"] = {
                "total": len(proj_bugs),
                "by_priority": proj_bugs["Priority"].value_counts().to_dict() if "Priority" in proj_bugs.columns else {},
                "by_status": proj_bugs["Status"].value_counts().to_dict() if "Status" in proj_bugs.columns else {},
                "overdue_sla": len(proj_bugs[proj_bugs["SLA Due date"] < pd.Timestamp.now()]) if "SLA Due date" in proj_bugs.columns else 0,
                "sample_bugs": proj_bugs[["Key", "Summary", "Priority", "Status"]].head(5).to_dict("records"),
            }

    # Milestones for this project
    if not milestones_df.empty and "Project Name" in milestones_df.columns:
        proj_ms = milestones_df[milestones_df["Project Name"].str.contains(project_name, case=False, na=False)]
        if not proj_ms.empty:
            project_data["milestones"] = {
                "total": len(proj_ms),
                "by_status": proj_ms["Status"].value_counts().to_dict() if "Status" in proj_ms.columns else {},
                "upcoming": proj_ms[["Key", "Summary", "Status", "Due date"]].head(5).to_dict("records"),
            }

    user_prompt = f"Analyze risks for this project:\n\n```json\n{json.dumps(project_data, default=str, indent=2)}\n```"
    return _call_claude(RISK_SYSTEM, user_prompt, max_tokens=800)


# ═══════════════════════════════════════════════════════════════════════════════
#  3. NATURAL LANGUAGE SEARCH — Convert questions to data filters
# ═══════════════════════════════════════════════════════════════════════════════

NL_SEARCH_SYSTEM = """You are a data query assistant for a project management dashboard.
The user will ask questions in natural language about their project data.

Available datasets and their columns:
- projects: Customer Name, Project Name, Project Region, Project Manager, Project Stage, Budget (USD), Planned Hours, Worked Hours, Burned %, % Complete, Billing Type
- bugs: Issue Type, Key, Summary, Assignee, Reporter, Priority (P1/P2/P3/P4), Status, Resolution, Created, Updated, Due date, SLA Due date, POD Name, Product Area, Project Name, Customer Name, Labels
- ers: Issue Type, Key, Summary, Assignee, Priority, Status, Product Area, Customer Name, Project Name, Customer Requested Month, Feature Impact
- milestones: Customer Name, Project Name, Issue Type, Key, Summary, Assignee, Status, Due date, Start date, Next Go-Live Date

Respond with ONLY a JSON object (no markdown, no explanation) in this format:
{
  "dataset": "projects|bugs|ers|milestones",
  "filters": [
    {"column": "column_name", "operator": "eq|ne|contains|gt|lt|gte|lte", "value": "filter_value"}
  ],
  "sort_by": "column_name or null",
  "sort_ascending": true,
  "columns_to_show": ["col1", "col2"] or null for all,
  "aggregation": null or {"type": "count|sum|mean|groupby", "column": "col", "group_by": "col"},
  "explanation": "Brief explanation of what this query does"
}

Be smart about mapping user language to column names. For example:
- "P1 bugs" → Priority == "P1"
- "HSBC project" → Customer Name contains "HSBC"
- "at risk" → look at stage/status fields
- "overdue" → Due date < today
- "highest bugs" → aggregate count grouped by something"""


def parse_nl_query(question: str, datasets: dict) -> dict:
    """Convert a natural language question into structured filters."""
    user_prompt = f"User question: {question}\n\nToday's date: {pd.Timestamp.now().strftime('%Y-%m-%d')}"
    response = _call_claude(NL_SEARCH_SYSTEM, user_prompt, max_tokens=500)

    # Strip markdown code fences if present
    response = response.strip()
    if response.startswith("```"):
        response = response.split("\n", 1)[1]
    if response.endswith("```"):
        response = response.rsplit("```", 1)[0]
    response = response.strip()

    try:
        result = json.loads(response)
        return result
    except json.JSONDecodeError:
        return {"error": f"Could not parse AI response: {response}"}


def execute_nl_query(query_spec: dict, datasets: dict) -> tuple[pd.DataFrame, str]:
    """Execute a parsed NL query against the actual data and return results + explanation."""
    if "error" in query_spec:
        return pd.DataFrame(), query_spec["error"]

    dataset_name = query_spec.get("dataset", "projects")
    df = datasets.get(dataset_name, pd.DataFrame())
    if df.empty:
        return df, f"No data available for '{dataset_name}'"

    explanation = query_spec.get("explanation", "")

    # Apply filters
    for f in query_spec.get("filters", []):
        col = f.get("column", "")
        op = f.get("operator", "eq")
        val = f.get("value", "")
        if col not in df.columns:
            continue
        if op == "eq":
            df = df[df[col].astype(str).str.lower() == str(val).lower()]
        elif op == "ne":
            df = df[df[col].astype(str).str.lower() != str(val).lower()]
        elif op == "contains":
            df = df[df[col].astype(str).str.lower().str.contains(str(val).lower(), na=False)]
        elif op in ("gt", "gte", "lt", "lte"):
            numeric_col = pd.to_numeric(df[col], errors="coerce")
            numeric_val = float(val)
            if op == "gt":
                df = df[numeric_col > numeric_val]
            elif op == "gte":
                df = df[numeric_col >= numeric_val]
            elif op == "lt":
                df = df[numeric_col < numeric_val]
            elif op == "lte":
                df = df[numeric_col <= numeric_val]

    # Apply sorting
    sort_col = query_spec.get("sort_by")
    if sort_col and sort_col in df.columns:
        df = df.sort_values(sort_col, ascending=query_spec.get("sort_ascending", True))

    # Apply column selection
    cols = query_spec.get("columns_to_show")
    if cols:
        valid_cols = [c for c in cols if c in df.columns]
        if valid_cols:
            df = df[valid_cols]

    # Apply aggregation
    agg = query_spec.get("aggregation")
    if agg and agg.get("type"):
        agg_type = agg["type"]
        agg_col = agg.get("column", "")
        group_col = agg.get("group_by", "")
        if agg_type == "count" and group_col and group_col in df.columns:
            df = df.groupby(group_col).size().reset_index(name="Count").sort_values("Count", ascending=False)
        elif agg_type == "sum" and agg_col in df.columns and group_col in df.columns:
            df = df.groupby(group_col)[agg_col].sum().reset_index().sort_values(agg_col, ascending=False)
        elif agg_type == "mean" and agg_col in df.columns and group_col in df.columns:
            df = df.groupby(group_col)[agg_col].mean().reset_index().sort_values(agg_col, ascending=False)

    return df, explanation
