// Place this file at app/claude-code/page.tsx in your Next.js app.
// Put the generated claude-code-stats.json in public/ so it imports at build time.
import type { Metadata } from "next";
import Link from "next/link";
import statsJson from "../../public/claude-code-stats.json";

export const metadata: Metadata = {
  title: "Claude Code — schlacter.me",
  description: "How much I ship with Claude Code. Monthly breakdown, hours, commits, projects.",
};

type TopProject = { label: string; hours: number; share: number };
type Month = {
  month: string;
  sessions: number;
  hours: number;
  avg_per_week_hours: number;
  max_session_hours: number;
  days_active: number;
  avg_length_min: number;
  commits: number;
  top_projects: TopProject[];
  partial: boolean;
};
type Stats = {
  generated_at: string;
  total: {
    hours: number;
    sessions: number;
    commits: number;
    days_active: number;
    first_month: string;
    latest_month: string;
  };
  months: Month[];
  suggestions: string[];
};

const stats = statsJson as Stats;

function fmtMonth(ym: string): string {
  const [y, m] = ym.split("-").map(Number);
  const d = new Date(Date.UTC(y, m - 1, 1));
  return d.toLocaleDateString("en-US", { month: "short", year: "numeric", timeZone: "UTC" });
}

function fmtDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export default function ClaudeCodePage() {
  const { total, months, suggestions } = stats;
  const monthsDesc = [...months].reverse();

  return (
    <div
      className="min-h-screen"
      style={{ background: "#F8F6F2", color: "#1A1A1A" }}
    >
      <main className="max-w-3xl mx-auto w-full px-6 pt-16 pb-16">
        <Link
          href="/"
          className="text-xs transition-opacity hover:opacity-50"
          style={{ color: "#8A8A8A" }}
        >
          ← schlacter.me
        </Link>

        <p
          className="text-xs tracking-widest uppercase mt-10"
          style={{ color: "#1A1A1A" }}
        >
          Claude Code
        </p>
        <h1 className="text-2xl mt-2" style={{ color: "#1A1A1A" }}>
          Power user since {fmtMonth(total.first_month)}
        </h1>
        <p className="text-sm mt-2" style={{ color: "#8A8A8A" }}>
          Everything I ship runs through Claude Code. Numbers update weekly.
        </p>

        <div
          className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-10 pt-8"
          style={{ borderTop: "1px solid #E5E1D8" }}
        >
          <Kpi label="hours" value={total.hours.toLocaleString(undefined, { maximumFractionDigits: 0 })} />
          <Kpi label="sessions" value={total.sessions.toLocaleString()} />
          <Kpi label="commits" value={total.commits.toLocaleString()} />
          <Kpi label="days active" value={total.days_active.toLocaleString()} />
        </div>

        <section className="mt-14">
          <p
            className="text-xs tracking-widest uppercase mb-4"
            style={{ color: "#8A8A8A" }}
          >
            Month by month
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr style={{ borderBottom: "1px solid #E5E1D8", color: "#8A8A8A" }}>
                  <th className="text-left py-2 pr-4 font-normal text-xs">Month</th>
                  <th className="text-right py-2 pr-4 font-normal text-xs">Sessions</th>
                  <th className="text-right py-2 pr-4 font-normal text-xs">Hours</th>
                  <th className="text-right py-2 pr-4 font-normal text-xs">Avg/wk</th>
                  <th className="text-right py-2 pr-4 font-normal text-xs">Days</th>
                  <th className="text-right py-2 pr-4 font-normal text-xs">Commits</th>
                  <th className="text-left py-2 font-normal text-xs">Top projects</th>
                </tr>
              </thead>
              <tbody>
                {monthsDesc.map((m) => (
                  <tr
                    key={m.month}
                    style={{ borderBottom: "1px solid #E5E1D8" }}
                  >
                    <td className="py-3 pr-4 whitespace-nowrap">
                      {fmtMonth(m.month)}
                      {m.partial && (
                        <span
                          className="text-xs ml-1.5"
                          style={{ color: "#8A8A8A" }}
                        >
                          (partial)
                        </span>
                      )}
                    </td>
                    <td className="py-3 pr-4 text-right tabular-nums">{m.sessions}</td>
                    <td className="py-3 pr-4 text-right tabular-nums">{m.hours}</td>
                    <td className="py-3 pr-4 text-right tabular-nums">{m.avg_per_week_hours}</td>
                    <td className="py-3 pr-4 text-right tabular-nums">{m.days_active}</td>
                    <td className="py-3 pr-4 text-right tabular-nums">{m.commits}</td>
                    <td
                      className="py-3 text-xs"
                      style={{ color: "#8A8A8A" }}
                    >
                      {m.top_projects
                        .filter((p) => p.hours > 0)
                        .slice(0, 3)
                        .map((p) => `${p.label} (${Math.round(p.share)}%)`)
                        .join(", ")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {suggestions.length > 0 && (
          <section className="mt-14">
            <p
              className="text-xs tracking-widest uppercase mb-4"
              style={{ color: "#8A8A8A" }}
            >
              Patterns worth naming
            </p>
            <div className="flex flex-wrap gap-2">
              {suggestions.map((s, i) => (
                <span
                  key={i}
                  className="text-xs px-3 py-1.5 rounded-full"
                  style={{
                    background: "#FFF",
                    border: "1px solid #E5E1D8",
                    color: "#1A1A1A",
                  }}
                >
                  {s}
                </span>
              ))}
            </div>
          </section>
        )}

        <section
          className="mt-14 pt-8 text-xs"
          style={{ borderTop: "1px solid #E5E1D8", color: "#8A8A8A" }}
        >
          <p>
            Methodology: sessions parsed from local Claude Code JSONL transcripts,
            capped at 6h each to avoid inflating on idle windows. Commits counted from
            projects linked to Claude sessions. Last synced {fmtDate(stats.generated_at)}.
          </p>
        </section>
      </main>

      <footer
        className="max-w-3xl mx-auto w-full px-6 py-8"
        style={{ borderTop: "1px solid #E5E1D8" }}
      >
        <p className="text-xs" style={{ color: "#8A8A8A" }}>
          vibed with love | oakland, ca
        </p>
      </footer>
    </div>
  );
}

function Kpi({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-2xl tabular-nums" style={{ color: "#1A1A1A" }}>
        {value}
      </p>
      <p
        className="text-xs tracking-widest uppercase mt-1"
        style={{ color: "#8A8A8A" }}
      >
        {label}
      </p>
    </div>
  );
}
