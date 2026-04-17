#!/usr/bin/env python3
"""
claude-code-insights aggregator.

Reads ~/.claude/projects/**/*.jsonl (Claude Code session transcripts) and produces
a stats.json summarizing monthly usage: hours, sessions, commits, top projects, etc.

Usage:
    python3 aggregator.py [--output PATH] [--labels PATH]

Defaults:
    --output  ~/schlacter-me/public/claude-code-stats.json
    --labels  project-labels.json (alongside this script)

Session duration is computed from first and last timestamp in the JSONL; capped
at 6h per session to filter idle gaps. Commits = occurrences of `git commit` in
Bash tool invocations.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

COMMIT_RE = re.compile(r"git\s+commit\b")
SESSION_CAP_SEC = 6 * 3600  # filter idle gaps
HOME = Path.home()
PROJECTS_DIR = HOME / ".claude" / "projects"


def find_jsonl_files():
    out = subprocess.check_output(
        ["find", str(PROJECTS_DIR), "-name", "*.jsonl", "-type", "f"],
        text=True,
    ).strip().split("\n")
    return [f for f in out if f]


def group_by_session(files):
    """Map session_id -> (project_dir, [jsonl_paths])."""
    sessions = defaultdict(lambda: {"proj": None, "files": []})
    for f in files:
        try:
            proj = f.split("/projects/")[1].split("/")[0]
        except IndexError:
            continue
        parts = f.split("/")
        sid = None
        for p in parts:
            if len(p) == 36 and p.count("-") == 4:
                sid = p
                break
        if not sid:
            sid = os.path.basename(f).replace(".jsonl", "")
        sessions[sid]["proj"] = proj
        sessions[sid]["files"].append(f)
    return sessions


def analyze_session(files):
    """Return (start_dt, duration_sec, commit_count) or None if session too short."""
    times = []
    commits = 0
    for f in files:
        try:
            with open(f) as fh:
                for line in fh:
                    try:
                        j = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    ts = j.get("timestamp")
                    if ts:
                        times.append(ts)
                    if j.get("type") == "assistant":
                        content = j.get("message", {}).get("content", [])
                        if isinstance(content, list):
                            for c in content:
                                if isinstance(c, dict) and c.get("type") == "tool_use" and c.get("name") == "Bash":
                                    cmd = c.get("input", {}).get("command", "") or ""
                                    commits += len(COMMIT_RE.findall(cmd))
        except OSError:
            continue
    if len(times) < 2:
        return None
    times.sort()
    try:
        t0 = datetime.fromisoformat(times[0].replace("Z", "+00:00"))
        t1 = datetime.fromisoformat(times[-1].replace("Z", "+00:00"))
    except ValueError:
        return None
    dur = (t1 - t0).total_seconds()
    if dur <= 0 or dur >= SESSION_CAP_SEC:
        # Still count commits; duration capped
        dur = min(dur, SESSION_CAP_SEC) if dur > 0 else 0
        if dur == 0:
            return None
    return t0, dur, commits


def weeks_in_month(year, month, today):
    """Return (weeks, partial_flag). Partial month (current) uses day_of_month/7."""
    import calendar
    days_in_month = calendar.monthrange(year, month)[1]
    if today.year == year and today.month == month:
        return today.day / 7.0, True
    return days_in_month / 7.0, False


def aggregate(labels_path):
    with open(labels_path) as fh:
        label_cfg = json.load(fh)
    labels = label_cfg["labels"]
    default_label = label_cfg.get("default", "other personal project")

    files = find_jsonl_files()
    sessions = group_by_session(files)

    by_month = defaultdict(lambda: {
        "sec": 0.0, "count": 0, "max_sec": 0.0,
        "days": set(), "commits": 0,
        "projects": defaultdict(float),
    })

    for sid, info in sessions.items():
        result = analyze_session(info["files"])
        if not result:
            continue
        t0, dur, commits = result
        key = t0.strftime("%Y-%m")
        m = by_month[key]
        m["sec"] += dur
        m["count"] += 1
        m["days"].add(t0.strftime("%Y-%m-%d"))
        m["commits"] += commits
        if dur > m["max_sec"]:
            m["max_sec"] = dur
        m["projects"][info["proj"]] += dur

    today = datetime.now(timezone.utc)
    months_out = []
    total_sec = 0.0
    total_sessions = 0
    total_commits = 0
    total_days = set()

    for key in sorted(by_month.keys()):
        m = by_month[key]
        year, mo = [int(x) for x in key.split("-")]
        weeks, partial = weeks_in_month(year, mo, today)
        hours = m["sec"] / 3600
        avg_per_week = hours / weeks if weeks else 0
        avg_len_min = m["sec"] / 60 / m["count"] if m["count"] else 0

        # Top projects, labeled + percentage
        proj_total = sum(m["projects"].values()) or 1
        top = sorted(m["projects"].items(), key=lambda x: -x[1])[:5]
        projects_out = [
            {
                "label": labels.get(proj, default_label),
                "hours": round(sec / 3600, 1),
                "share": round(sec / proj_total * 100, 1),
            }
            for proj, sec in top
        ]

        months_out.append({
            "month": key,
            "sessions": m["count"],
            "hours": round(hours, 1),
            "avg_per_week_hours": round(avg_per_week, 1),
            "max_session_hours": round(m["max_sec"] / 3600, 2),
            "days_active": len(m["days"]),
            "avg_length_min": round(avg_len_min),
            "commits": m["commits"],
            "top_projects": projects_out,
            "partial": partial,
        })
        total_sec += m["sec"]
        total_sessions += m["count"]
        total_commits += m["commits"]
        total_days |= m["days"]

    total = {
        "hours": round(total_sec / 3600, 1),
        "sessions": total_sessions,
        "commits": total_commits,
        "days_active": len(total_days),
        "first_month": months_out[0]["month"] if months_out else None,
        "latest_month": months_out[-1]["month"] if months_out else None,
    }

    return {
        "generated_at": today.isoformat(timespec="seconds"),
        "total": total,
        "months": months_out,
        "suggestions": [],  # populated by insight-detector.py
    }


def main():
    script_dir = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default=str(HOME / "schlacter-me" / "public" / "claude-code-stats.json"))
    ap.add_argument("--labels", default=str(script_dir / "project-labels.json"))
    args = ap.parse_args()

    data = aggregate(args.labels)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as fh:
        json.dump(data, fh, indent=2)
    t = data["total"]
    print(f"Wrote {output_path}")
    print(f"Total: {t['hours']}h, {t['sessions']} sessions, {t['commits']} commits, {t['days_active']} days active")
    print(f"Months: {len(data['months'])} ({data['total']['first_month']} → {data['total']['latest_month']})")


if __name__ == "__main__":
    main()
