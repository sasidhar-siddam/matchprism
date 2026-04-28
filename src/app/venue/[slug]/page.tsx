import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getVenue, getAllVenueSlugs, getSchedule, venueToSlug } from "@/lib/data";
import { getTeam, getTeamColorClass } from "@/lib/teams";
import type { TeamCode, Grade } from "@/lib/types";
import { GradeBadge } from "@/components/GradeBadge";

export function generateStaticParams() {
  return getAllVenueSlugs().map((slug) => ({ slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const venue = getVenue(slug);
  const name = venue?.name ?? "Venue";
  const city = venue?.city ?? "";
  return {
    title: `${name} | Venue Intelligence | MatchPrism`,
    description: `Deep-dive venue analytics for ${name}, ${city}. ${venue?.totalMatches ?? 0} matches analysed with phase dynamics, toss intelligence, and specialist impact data.`,
  };
}

/* ───────────────────────────────────────────
   Progress Bar
   ─────────────────────────────────────────── */
function ProgressBar({
  value,
  max = 100,
  accent = false,
}: {
  value: number;
  max?: number;
  accent?: boolean;
}) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div className="w-full h-2 rounded-full bg-surface-container-highest overflow-hidden">
      <div
        className={`h-full rounded-full transition-all ${
          accent ? "bg-primary-container" : "bg-outline"
        }`}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

/* ───────────────────────────────────────────
   Page Component
   ─────────────────────────────────────────── */
export default async function VenuePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const venue = getVenue(slug);
  if (!venue) return notFound();

  const batFirstPct = 100 - (venue.chaseWinPct ?? 50);
  const bowlFirstPct = venue.chaseWinPct ?? 50;

  // Pace/spin percentages from real data
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const venueAny = venue as any;
  const pacePct: number = venueAny.paceWicketPct ?? 60;
  const spinPct: number = venueAny.spinWicketPct ?? 40;

  // Placeholder specialist players (use venue pace/spin stats instead of hardcoded players)
  const siraj = { name: "Pace Specialist", team: "RCB" as TeamCode, venueSR: "-", venueEcon: "-", grade: "B" as Grade };
  const maxwell = { name: "Spin Specialist", team: "RCB" as TeamCode, venueSR: "-", venueAvg: "-", grade: "B" as Grade };

  // Get schedule matches at this venue
  const schedule = getSchedule();
  const upcomingMatches = schedule.map((s) => ({
    slug: s.slug,
    date: s.date,
    time: s.time,
    team1: s.team1 as TeamCode,
    team2: s.team2 as TeamCode,
    venue: s.venue,
    probability: `${s.team1WinProb}% vs ${s.team2WinProb}%`,
    confidenceLabel: s.modelConfidence > 85 ? "High Confidence Insight" : s.modelConfidence > 70 ? "Moderate Confidence Insight" : undefined,
  }));

  return (
    <div className="space-y-10 pb-12">
      {/* ═══════════════════════════════════════════
          SECTION 1: Venue Header
         ═══════════════════════════════════════════ */}
      <section className="relative -mx-4 md:-mx-8 -mt-4 overflow-hidden">
        {/* Dark gradient background */}
        <div className="bg-surface-container rounded-3xl mx-4 md:mx-8 overflow-hidden relative">
          {/* Radial gradient overlay */}
          <div
            className="absolute inset-0 opacity-30"
            style={{
              background:
                "radial-gradient(ellipse at 30% 20%, var(--color-primary-container), transparent 60%), radial-gradient(ellipse at 70% 80%, var(--color-surface-bright), transparent 50%)",
            }}
          />
          {/* Subtle grid pattern */}
          <div
            className="absolute inset-0 opacity-[0.04]"
            style={{
              backgroundImage:
                "linear-gradient(var(--color-on-surface) 1px, transparent 1px), linear-gradient(90deg, var(--color-on-surface) 1px, transparent 1px)",
              backgroundSize: "48px 48px",
            }}
          />

          <div className="relative z-10 flex flex-col items-center py-12 px-6 md:py-16">
            {/* Premium badge */}
            <span className="inline-block text-[11px] font-semibold tracking-[0.2em] uppercase text-primary bg-primary/10 px-4 py-1.5 rounded-full mb-6">
              Premium Intelligence Center
            </span>

            {/* Venue name */}
            <h1 className="font-headline text-3xl md:text-5xl font-black text-on-surface text-center leading-tight mb-3">
              {venue.name}
            </h1>

            {/* Location */}
            <div className="flex items-center gap-2 mb-8">
              <svg
                className="w-4 h-4 text-outline"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 0115 0z"
                />
              </svg>
              <span className="text-sm text-secondary tracking-wide">
                {venue.city}, India
              </span>
            </div>

            {/* Evidence sample box */}
            <div className="bg-surface-container-high/60 backdrop-blur-xl rounded-xl px-6 py-3.5 border border-outline-variant/30">
              <span className="text-[11px] uppercase tracking-[0.15em] text-outline block mb-1 text-center">
                Evidence Sample
              </span>
              <span className="font-headline text-lg md:text-xl font-bold text-on-surface block text-center">
                {venue.totalMatches} Matches Analysed
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          SECTION 2: Key Metrics Row
         ═══════════════════════════════════════════ */}
      <section>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Avg 1st Innings Score */}
          <div className="bg-surface-container rounded-2xl p-6">
            <span className="text-[11px] uppercase tracking-[0.15em] text-outline block mb-3">
              Avg 1st Inn Score
            </span>
            <span className="font-headline text-4xl md:text-5xl font-black text-on-surface block">
              {venue.avg1stInnings}
            </span>
            <span className="text-sm text-tertiary-fixed-dim font-medium mt-1 block">
              +8.2 vs League Avg
            </span>
          </div>

          {/* Venue Run Rate */}
          <div className="bg-surface-container rounded-2xl p-6">
            <span className="text-[11px] uppercase tracking-[0.15em] text-outline block mb-3">
              Venue Run Rate
            </span>
            <span className="font-headline text-4xl md:text-5xl font-black text-on-surface block">
              {venue.venueRunRate}
            </span>
            <span className="inline-block text-[11px] font-semibold tracking-[0.1em] uppercase text-on-primary bg-primary-container px-3 py-1 rounded-full mt-2">
              High Octane
            </span>
          </div>

          {/* Boundaries Per Innings */}
          <div className="bg-surface-container rounded-2xl p-6">
            <span className="text-[11px] uppercase tracking-[0.15em] text-outline block mb-3">
              Boundaries Per Inn
            </span>
            <span className="font-headline text-4xl md:text-5xl font-black text-on-surface block">
              {venue.boundariesPerInnings}
            </span>
            <span className="text-sm text-secondary mt-1 block">
              14 Sixes / 10.6 Fours
            </span>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          SECTION 3: Toss Intelligence + Phase Dynamics
         ═══════════════════════════════════════════ */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Toss Intelligence */}
        <div className="bg-surface-container rounded-2xl p-6 space-y-5">
          <h2 className="font-headline text-xl font-bold text-on-surface">
            Toss Intelligence
          </h2>

          {/* Win Batting First */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm text-secondary">Win Batting First</span>
              <span className="font-headline text-sm font-bold text-on-surface">
                {batFirstPct}%
              </span>
            </div>
            <ProgressBar value={batFirstPct} accent={false} />
          </div>

          {/* Win Bowling First */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm text-secondary">Win Bowling First</span>
              <span className="font-headline text-sm font-bold text-primary">
                {bowlFirstPct}%
              </span>
            </div>
            <ProgressBar value={bowlFirstPct} accent={true} />
          </div>

          {/* Oracle Analysis Callout */}
          <div className="bg-surface-container-high rounded-xl p-4 border border-outline-variant/20">
            <span className="text-[11px] uppercase tracking-[0.12em] text-primary block mb-1.5">
              Oracle Analysis
            </span>
            <p className="text-sm text-secondary leading-relaxed">
              Strong chase bias due to small boundaries and evening dew factor.
            </p>
          </div>
        </div>

        {/* Phase Dynamics */}
        <div className="bg-surface-container rounded-2xl p-6 space-y-5">
          <h2 className="font-headline text-xl font-bold text-on-surface">
            Phase Dynamics
          </h2>

          <div className="grid grid-cols-3 gap-4">
            {/* Powerplay */}
            <div className="text-center space-y-2">
              <span className="text-[11px] uppercase tracking-[0.12em] text-outline block">
                Powerplay
              </span>
              <span className="text-[12px] text-secondary block">
                Overs 1-6
              </span>
              <span className="font-headline text-2xl md:text-3xl font-black text-on-surface block">
                {venue.powerplayAvg}
              </span>
              <span className="text-[11px] text-outline block">avg runs</span>
              <span className="inline-block text-[11px] text-tertiary-fixed-dim font-medium bg-tertiary-fixed-dim/10 px-2.5 py-1 rounded-full">
                Low Wicket Risk
              </span>
            </div>

            {/* Middle Overs */}
            <div className="text-center space-y-2">
              <span className="text-[11px] uppercase tracking-[0.12em] text-outline block">
                Middle
              </span>
              <span className="text-[12px] text-secondary block">
                Overs 7-15
              </span>
              <span className="font-headline text-2xl md:text-3xl font-black text-on-surface block">
                {venue.middleOversAvg}
              </span>
              <span className="text-[11px] text-outline block">avg runs</span>
              <span className="inline-block text-[11px] text-secondary font-medium bg-secondary/10 px-2.5 py-1 rounded-full">
                Steady Rotation
              </span>
            </div>

            {/* Death Overs */}
            <div className="text-center space-y-2">
              <span className="text-[11px] uppercase tracking-[0.12em] text-outline block">
                Death
              </span>
              <span className="text-[12px] text-secondary block">
                Overs 16-20
              </span>
              <span className="font-headline text-2xl md:text-3xl font-black text-on-surface block">
                {venue.deathOversAvg}
              </span>
              <span className="text-[11px] text-outline block">avg runs</span>
              <span className="inline-block text-[11px] text-primary font-medium bg-primary/10 px-2.5 py-1 rounded-full">
                Extreme Acceleration
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          SECTION 4: Specialist Impact
         ═══════════════════════════════════════════ */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Pace Impact */}
        <div className="bg-surface-container rounded-2xl p-6 space-y-5">
          <div className="flex items-baseline justify-between">
            <h2 className="font-headline text-xl font-bold text-on-surface">
              Pace Impact
            </h2>
            <span className="font-headline text-2xl font-black text-primary">
              {venue.paceWicketPct}%
              <span className="text-sm font-medium text-secondary ml-1">
                Wickets
              </span>
            </span>
          </div>

          {/* Featured Player: Siraj */}
          <div className="bg-surface-container-high rounded-xl p-4 border border-outline-variant/20">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0">
                <span
                  className={`inline-block w-3 h-3 rounded-full ${getTeamColorClass(
                    siraj.team
                  )}`}
                />
              </div>
              <div className="flex-1">
                <h3 className="font-headline text-base font-bold text-on-surface">
                  {siraj.name}
                </h3>
                <p className="text-[13px] text-secondary mt-0.5">
                  Fast Bowler
                </p>
                <div className="flex items-center gap-4 mt-3">
                  <div>
                    <span className="text-[11px] uppercase tracking-[0.12em] text-outline block">
                      Venue SR
                    </span>
                    <span className="font-headline text-lg font-bold text-on-surface">
                      {siraj.venueSR}
                    </span>
                  </div>
                  <div>
                    <span className="text-[11px] uppercase tracking-[0.12em] text-outline block">
                      Venue Econ
                    </span>
                    <span className="font-headline text-lg font-bold text-on-surface">
                      {siraj.venueEcon}
                    </span>
                  </div>
                  <div className="ml-auto">
                    <GradeBadge grade={siraj.grade} size="sm" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Spin Resilience */}
        <div className="bg-surface-container rounded-2xl p-6 space-y-5">
          <div className="flex items-baseline justify-between">
            <h2 className="font-headline text-xl font-bold text-on-surface">
              Spin Resilience
            </h2>
            <span className="font-headline text-2xl font-black text-primary">
              {venue.spinWicketPct}%
              <span className="text-sm font-medium text-secondary ml-1">
                Wickets
              </span>
            </span>
          </div>

          {/* Featured Player: Maxwell */}
          <div className="bg-surface-container-high rounded-xl p-4 border border-outline-variant/20">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0">
                <span
                  className={`inline-block w-3 h-3 rounded-full ${getTeamColorClass(
                    maxwell.team
                  )}`}
                />
              </div>
              <div className="flex-1">
                <h3 className="font-headline text-base font-bold text-on-surface">
                  {maxwell.name}
                </h3>
                <p className="text-[13px] text-secondary mt-0.5">
                  Spin / All-Rounder
                </p>
                <div className="flex items-center gap-4 mt-3">
                  <div>
                    <span className="text-[11px] uppercase tracking-[0.12em] text-outline block">
                      Venue SR
                    </span>
                    <span className="font-headline text-lg font-bold text-on-surface">
                      {maxwell.venueSR}
                    </span>
                  </div>
                  <div>
                    <span className="text-[11px] uppercase tracking-[0.12em] text-outline block">
                      Venue Avg
                    </span>
                    <span className="font-headline text-lg font-bold text-on-surface">
                      {maxwell.venueAvg}
                    </span>
                  </div>
                  <div className="ml-auto">
                    <GradeBadge grade={maxwell.grade} size="sm" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          SECTION 5: Upcoming Intelligence Targets
         ═══════════════════════════════════════════ */}
      <section>
        <div className="flex items-baseline justify-between mb-1">
          <h2 className="font-headline text-xl md:text-2xl font-bold text-on-surface">
            Upcoming Intelligence Targets
          </h2>
          <span className="text-[11px] uppercase tracking-[0.12em] text-outline">
            IPL 2026
          </span>
        </div>
        <p className="text-secondary text-sm mb-6">
          Matches with venue intelligence available.
        </p>

        <div className="flex overflow-x-auto gap-6 pb-4 -mx-4 px-4 md:-mx-0 md:px-0 scrollbar-none">
          {upcomingMatches.map((match, idx) => {
            const t1Color = getTeamColorClass(match.team1);
            const t2Color = getTeamColorClass(match.team2);
            const hasProb = !!match.probability;
            const isHighConf =
              match.confidenceLabel?.toLowerCase().includes("high");

            return (
              <div
                key={match.slug}
                className="bg-surface-container rounded-2xl p-5 min-w-[260px] max-w-[300px] flex-shrink-0 flex flex-col justify-between"
              >
                {/* Header */}
                <div>
                  <span className="text-[11px] uppercase tracking-[0.15em] text-outline block mb-1">
                    Match {idx + 1} &middot; IPL 2026
                  </span>
                  <span className="text-[13px] text-secondary block mb-4">
                    {match.date} &middot; {match.time}
                  </span>

                  {/* Teams */}
                  <div className="flex items-center gap-3 mb-4">
                    <div className="flex items-center gap-2">
                      <span
                        className={`inline-block w-3 h-3 rounded-full ${t1Color}`}
                      />
                      <span className="font-headline text-base font-bold text-on-surface">
                        {match.team1}
                      </span>
                    </div>
                    <span className="text-sm text-outline">vs</span>
                    <div className="flex items-center gap-2">
                      <span
                        className={`inline-block w-3 h-3 rounded-full ${t2Color}`}
                      />
                      <span className="font-headline text-base font-bold text-on-surface">
                        {match.team2}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Probability + Confidence */}
                <div className="border-t border-outline-variant/15 pt-3 space-y-2.5">
                  {hasProb ? (
                    <div>
                      <span className="text-[11px] uppercase tracking-[0.12em] text-outline block mb-1">
                        Probability
                      </span>
                      <span className="text-sm font-semibold text-primary">
                        {match.probability}
                      </span>
                    </div>
                  ) : (
                    <div>
                      <span className="text-[11px] uppercase tracking-[0.12em] text-outline block mb-1">
                        Probability
                      </span>
                      <span className="text-sm text-secondary">
                        Pending Analysis
                      </span>
                    </div>
                  )}

                  {match.confidenceLabel ? (
                    <span
                      className={`inline-block text-[11px] font-medium px-2.5 py-1 rounded-full ${
                        isHighConf
                          ? "bg-tertiary-fixed-dim/15 text-tertiary-fixed-dim"
                          : "bg-grade-b/15 text-grade-b"
                      }`}
                    >
                      {match.confidenceLabel}
                    </span>
                  ) : (
                    <span className="inline-block text-[11px] font-medium px-2.5 py-1 rounded-full bg-secondary/10 text-secondary">
                      Awaiting Data
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
