import Link from "next/link";
import { getWCSchedule } from "@/lib/worldcup";
import type { WCMatch } from "@/lib/worldcup";
import { LocalTime } from "@/components/LocalTime";

export const metadata = {
  title: "World Cup 2026 Fixtures | MatchPrism",
  description: "All 104 FIFA World Cup 2026 fixtures with venues, kickoff times and results.",
};

const STAGE_ORDER = [
  "Group Stage",
  "Round of 32",
  "Round of 16",
  "Quarter-final",
  "Semi-final",
  "Third Place",
  "Final",
];

function MatchRow({ m }: { m: WCMatch }) {
  const played = m.status === "played";
  return (
    <div className="bg-surface-container rounded-2xl p-4 flex items-center justify-between gap-4">
      <div className="min-w-0">
        <span className="font-headline text-base font-bold text-on-surface">
          {m.homeTeam}{" "}
          {played ? (
            <span className="text-primary">
              {m.homeScore}–{m.awayScore}
            </span>
          ) : (
            <span className="font-light text-outline">vs</span>
          )}{" "}
          {m.awayTeam}
        </span>
        <p className="text-[13px] text-secondary mt-0.5 truncate">
          {m.venue}
          {m.group ? ` · ${m.group}` : ""}
          {m.matchday ? ` · Matchday ${m.matchday}` : ""}
        </p>
      </div>
      <div className="text-right flex-shrink-0">
        <p className="text-[13px] font-medium text-on-surface-variant">{m.date}</p>
        {played ? (
          <p className="text-[11px] uppercase tracking-[0.1em] text-grade-aplus font-medium">
            Full Time
          </p>
        ) : (
          <p className="text-[11px] text-outline">
            {m.time} <LocalTime date={m.dateRaw} time={m.time} className="block text-[11px] text-outline/70" />
          </p>
        )}
      </div>
    </div>
  );
}

export default function WorldCupMatchesPage() {
  const schedule = getWCSchedule();

  if (!schedule) {
    return (
      <div className="py-20 text-center">
        <p className="text-sm text-secondary">
          Fixture data not generated yet. Run{" "}
          <code className="text-primary">python scripts/worldcup_fetch_fixtures.py</code>.
        </p>
      </div>
    );
  }

  const byStage = new Map<string, WCMatch[]>();
  for (const m of schedule.matches) {
    if (!byStage.has(m.stage)) byStage.set(m.stage, []);
    byStage.get(m.stage)!.push(m);
  }

  return (
    <div className="space-y-10 pb-12">
      <header className="pt-4">
        <Link
          href="/worldcup"
          className="text-primary text-sm font-medium hover:underline"
        >
          &larr; World Cup Hub
        </Link>
        <h1 className="font-headline text-2xl md:text-3xl font-bold text-on-surface mt-3">
          World Cup 2026 Fixtures
        </h1>
        <p className="text-secondary text-sm mt-1">
          {schedule.totalMatches} matches &middot; {schedule.playedMatches}{" "}
          played &middot; 16 host cities across USA, Mexico and Canada
        </p>
      </header>

      {STAGE_ORDER.filter((s) => byStage.has(s)).map((stage) => {
        const matches = byStage.get(stage)!;
        return (
          <section key={stage}>
            <div className="flex items-baseline justify-between mb-4">
              <h2 className="font-headline text-xl font-bold text-on-surface">{stage}</h2>
              <span className="text-[11px] uppercase tracking-[0.12em] text-outline">
                {matches.length} {matches.length === 1 ? "match" : "matches"}
              </span>
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
              {matches.map((m) => (
                <MatchRow key={m.slug} m={m} />
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}
