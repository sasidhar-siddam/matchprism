import Link from "next/link";
import fs from "fs";
import path from "path";
import { nameToSlug } from "@/lib/data";
import { GradeBadge } from "@/components/GradeBadge";
import type { Grade } from "@/lib/types";

export const metadata = {
  title: "T20 Players | MatchPrism",
  description:
    "Browse 5,700+ T20 cricket players across IPL, BBL, PSL, CPL, SA20, T20I and more. Form trends, venue grades, and career analytics.",
};

interface PlayerSummary {
  name: string;
  slug: string;
  teams: string[];
  leagues: string[];
  runs: number;
  innings: number;
  average: number;
  strikeRate: number;
  wickets: number;
  bowlInnings: number;
  role: string;
  trend: string;
}

function loadPlayers(): PlayerSummary[] {
  const playersPath = path.join(process.cwd(), "data", "processed", "players.json");
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const raw: Record<string, any> = JSON.parse(fs.readFileSync(playersPath, "utf-8"));

  const players: PlayerSummary[] = [];
  for (const [name, data] of Object.entries(raw)) {
    const bat = data.overall?.batting ?? {};
    const bowl = data.overall?.bowling ?? {};
    const batInn = bat.innings ?? 0;
    const bowlInn = bowl.innings ?? 0;

    // Only include players with 20+ T20 innings
    if (batInn + bowlInn < 20) continue;

    let role = "Batter";
    if (bowlInn > batInn) role = "Bowler";
    else if (bowlInn > 0 && bowlInn / Math.max(batInn, 1) > 0.5) role = "All-rounder";

    players.push({
      name,
      slug: nameToSlug(name),
      teams: data.teams ?? [],
      leagues: data.leagues ?? [],
      runs: bat.runs ?? 0,
      innings: batInn,
      average: bat.average ?? 0,
      strikeRate: bat.strikeRate ?? 0,
      wickets: bowl.wickets ?? 0,
      bowlInnings: bowlInn,
      role,
      trend: data.recentForm?.trend ?? "consistent",
    });
  }

  // Sort by runs descending
  players.sort((a, b) => b.runs - a.runs);
  return players;
}

const LEAGUE_LABELS: Record<string, string> = {
  ipl: "IPL",
  bbl: "BBL",
  psl: "PSL",
  cpl: "CPL",
  sa20: "SA20",
  t20i: "T20I",
  bpl: "BPL",
  lpl: "LPL",
  ilt20: "ILT20",
  mlc: "MLC",
  the_hundred: "100",
  npl: "NPL",
};

export default function PlayersPage() {
  const players = loadPlayers();

  // Group by role
  const batters = players.filter((p) => p.role === "Batter").slice(0, 80);
  const bowlers = players.filter((p) => p.role === "Bowler").slice(0, 60);
  const allrounders = players.filter((p) => p.role === "All-rounder").slice(0, 40);

  return (
    <div className="py-8 space-y-10">
      <div>
        <h1 className="font-headline text-3xl md:text-4xl font-black text-on-surface">
          Player Intelligence
        </h1>
        <p className="text-secondary mt-2">
          {players.length.toLocaleString()} players across 12 T20 leagues worldwide.
          Tap any player for full venue analytics, form trends, and opposition quality data.
        </p>
        <p className="text-[13px] text-outline mt-1">
          Data covers: IPL, BBL, PSL, CPL, SA20, ILT20, BPL, LPL, MLC, The Hundred, NPL, and T20 Internationals.
        </p>
      </div>

      {/* Batters */}
      <section>
        <h2 className="font-headline text-xl font-bold text-on-surface mb-4">
          Top Batters <span className="text-secondary font-normal text-base">by career T20 runs</span>
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
          {batters.map((p) => (
            <PlayerCard key={p.slug} player={p} statLabel="Runs" statValue={p.runs.toLocaleString()} secondaryStat={`Avg ${p.average.toFixed(1)} · SR ${p.strikeRate.toFixed(1)}`} />
          ))}
        </div>
      </section>

      {/* Bowlers */}
      <section>
        <h2 className="font-headline text-xl font-bold text-on-surface mb-4">
          Top Bowlers <span className="text-secondary font-normal text-base">by career T20 wickets</span>
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
          {bowlers.sort((a, b) => b.wickets - a.wickets).map((p) => (
            <PlayerCard key={p.slug} player={p} statLabel="Wickets" statValue={String(p.wickets)} secondaryStat={`${p.bowlInnings} innings`} />
          ))}
        </div>
      </section>

      {/* All-rounders */}
      <section>
        <h2 className="font-headline text-xl font-bold text-on-surface mb-4">
          All-rounders <span className="text-secondary font-normal text-base">bat + bowl</span>
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
          {allrounders.map((p) => (
            <PlayerCard key={p.slug} player={p} statLabel="Runs" statValue={p.runs.toLocaleString()} secondaryStat={`${p.wickets} wkts · SR ${p.strikeRate.toFixed(1)}`} />
          ))}
        </div>
      </section>
    </div>
  );
}

function PlayerCard({
  player,
  statLabel,
  statValue,
  secondaryStat,
}: {
  player: PlayerSummary;
  statLabel: string;
  statValue: string;
  secondaryStat: string;
}) {
  return (
    <Link
      href={`/player/${player.slug}`}
      className="bg-surface-container rounded-xl p-4 hover:bg-surface-container-high transition-colors group flex justify-between items-start"
    >
      <div className="min-w-0">
        <h3 className="font-headline font-bold text-on-surface group-hover:text-primary transition-colors truncate">
          {player.name}
        </h3>
        <p className="text-[12px] text-secondary mt-0.5 truncate">
          {player.teams.slice(-2).join(", ")}
        </p>
        <div className="flex gap-1 mt-2 flex-wrap">
          {player.leagues.slice(0, 4).map((l) => (
            <span
              key={l}
              className="text-[11px] bg-surface-container-highest px-1.5 py-0.5 rounded text-secondary uppercase"
            >
              {LEAGUE_LABELS[l] ?? l}
            </span>
          ))}
          {player.leagues.length > 4 && (
            <span className="text-[11px] text-outline">+{player.leagues.length - 4}</span>
          )}
        </div>
      </div>
      <div className="text-right ml-3 shrink-0">
        <p className="text-[11px] text-outline uppercase">{statLabel}</p>
        <p className="font-headline font-bold text-primary text-lg">{statValue}</p>
        <p className="text-[12px] text-secondary">{secondaryStat}</p>
        {player.trend !== "consistent" && (
          <span className={`text-[11px] font-medium ${player.trend === "improving" ? "text-grade-aplus" : "text-grade-d"}`}>
            {player.trend === "improving" ? "Form Up" : "Form Down"}
          </span>
        )}
      </div>
    </Link>
  );
}
