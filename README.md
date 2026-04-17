# claude-code-insights-dashboard

Turn your local Claude Code session transcripts into a public stats page.

Parses `~/.claude/projects/**/*.jsonl` (the JSONL transcripts Claude Code writes for every session) into a monthly breakdown of hours, sessions, commits, days active, and top projects. Drop the output into a Next.js page and you've got a public stats page like [schlacter.me/claude-code](https://schlacter.me/claude-code).

## What's in here

- `aggregator.py` — parses JSONL transcripts, writes `claude-code-stats.json`. Session duration capped at 6h to filter idle gaps. Commits counted from `git commit` in Bash tool invocations.
- `insight-detector.py` — **stub**. Emits `suggestions[]` (empty). Intended for v2 pattern mining ("you refactor more than you build", etc.).
- `project-labels.example.json` — map raw project dir names to anonymized public labels.
- `next-dashboard-example/page.tsx` — Next.js App Router server component. Copy to `app/claude-code/page.tsx` and drop `claude-code-stats.json` in `public/`.
- `render_social_image.py` — Renders a 1200×1200 PNG social share card from `claude-code-stats.json`. Requires Pillow (`pip install Pillow`).

## Quickstart

```bash
# 1. Clone
git clone https://github.com/hbschlac/claude-code-insights-dashboard.git
cd claude-code-insights-dashboard

# 2. Copy labels file and edit with your own project mappings
cp project-labels.example.json project-labels.json
# (optional) edit project-labels.json

# 3. Generate stats
python3 aggregator.py --output ./claude-code-stats.json

# 4. Check output
cat claude-code-stats.json | head -30
```

## Wire it into a Next.js site

```bash
# From your Next.js app root:
cp path/to/claude-code-insights-dashboard/next-dashboard-example/page.tsx app/claude-code/page.tsx
cp path/to/claude-code-stats.json public/claude-code-stats.json
```

The page imports the JSON at build time so there's no runtime read. To refresh, regenerate the JSON and redeploy.

## Automate the weekly refresh

In a Claude Code scheduled task, or cron, or GitHub Action:

```bash
python3 aggregator.py --output ~/your-site/public/claude-code-stats.json
python3 insight-detector.py
cd ~/your-site
git add public/claude-code-stats.json
git commit -m "weekly claude-code stats refresh"
git push
```

## Methodology

- **Session** = one JSONL file. **Duration** = `last_ts − first_ts`, capped at 6h. Capping is more accurate than rejecting long sessions outright — a session with real idle time still has real work in it.
- **Commits** = occurrences of `git commit` in Bash tool invocations within the JSONL.
- **Days active** = distinct UTC dates with at least one session.
- `partial: true` on the latest month means the month isn't over yet.

## License

MIT. Do whatever.
