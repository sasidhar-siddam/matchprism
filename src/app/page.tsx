import Link from "next/link";
import { getSchedule, getMatch } from "@/lib/data";
import { getTeam, getTeamColorClass } from "@/lib/teams";
import type { TeamCode, Grade } from "@/lib/types";
import { GradeBadge } from "@/components/GradeBadge";
import { Countdown } from "@/components/Countdown";
import { LocalTime } from "@/components/LocalTime";

export default function HomePage() {
  const schedule = getSchedule();
  const featured = getMatch(schedule[0]?.slug || "rcb-vs-srh")!;
  const upcomingMatches = schedule.slice(1).map((s) => ({
    slug: s.slug,
    date: s.date,
    time: s.time,
    team1: s.team1 as TeamCode,
    team2: s.team2 as TeamCode,
    venue: `${s.venue}, ${s.city}`,
    probability: `${s.team1WinProb}% vs ${s.team2WinProb}%`,
    confidenceLabel:
      s.modelConfidence > 85
        ? "High Confidence Insight"
        : s.modelConfidence > 70
          ? "Moderate Confidence Insight"
          : undefined,
  }));
  const captainPicks = featured?.captainPicks || [];

  return (
    <div className="space-y-10 pb-12">
      {/* ═══════════════════════════════════════════
          HERO — Featured Match
         ═══════════════════════════════════════════ */}
      <section className="relative -mx-4 md:-mx-8 -mt-4 overflow-hidden">
        {/* Gradient background */}
        <div
          className="absolute inset-0"
          style={{
            background:
              "linear-gradient(135deg, var(--color-surface-container-low) 0%, var(--color-surface) 40%, var(--color-surface-container-low) 70%, var(--color-surface) 100%)",
          }}
        />
        {/* Team color accents */}
        <div
          className="absolute inset-0 opacity-[0.08]"
          style={{
            background:
              "radial-gradient(ellipse at 25% 50%, var(--color-team-rcb), transparent 60%), radial-gradient(ellipse at 75% 50%, var(--color-team-srh), transparent 60%)",
          }}
        />
        {/* Subtle grid overlay */}
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage:
              "linear-gradient(var(--color-on-surface) 1px, transparent 1px), linear-gradient(90deg, var(--color-on-surface) 1px, transparent 1px)",
            backgroundSize: "40px 40px",
          }}
        />

        <div className="relative z-10 flex flex-col items-center py-14 px-4 md:py-20">
          {/* Live badge */}
          <div className="flex items-center gap-2 mb-4">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary-container opacity-75" />
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-primary-container" />
            </span>
            <span className="text-[11px] font-semibold tracking-[0.15em] uppercase text-primary">
              Live Probability
            </span>
          </div>

          {/* Venue */}
          <p className="text-secondary text-sm tracking-wide mb-6">
            {featured.venue.name}
          </p>

          {/* Team names */}
          <div className="flex items-center gap-4 md:gap-6 mb-2">
            <span
              className="font-headline text-4xl md:text-6xl font-black tracking-tight"
              style={{ color: "var(--color-team-rcb)" }}
            >
              {featured.team1}
            </span>
            <span className="font-headline text-2xl md:text-4xl font-light text-outline">
              vs
            </span>
            <span
              className="font-headline text-4xl md:text-6xl font-black tracking-tight"
              style={{ color: "var(--color-team-srh)" }}
            >
              {featured.team2}
            </span>
          </div>

          {/* Subtitle labels */}
          <div className="flex items-center gap-8 md:gap-16 mb-8">
            <span className="text-[11px] uppercase tracking-[0.2em] text-on-surface-variant">
              {getTeam(featured.team1).shortName}
            </span>
            <span className="text-[11px] uppercase tracking-[0.2em] text-on-surface-variant">
              {getTeam(featured.team2).shortName}
            </span>
          </div>

          {/* Live countdown timer */}
          <Countdown targetDate={featured.dateRaw} targetTime={featured.time} />

          {/* Match date / time */}
          <p className="mt-5 text-[13px] text-outline">
            {featured.date} &middot; {featured.time}{" "}
            <LocalTime date={featured.dateRaw} time={featured.time} />
          </p>

          {/* CTA */}
          <Link
            href={`/match/${featured.slug}`}
            className="mt-6 inline-flex items-center gap-2 bg-primary/10 hover:bg-primary/20 text-primary text-sm font-semibold px-6 py-2.5 rounded-full transition-colors"
          >
            View Full Analysis
            <svg
              className="w-4 h-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M13 7l5 5m0 0l-5 5m5-5H6"
              />
            </svg>
          </Link>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          INTELLIGENCE PICKS
         ═══════════════════════════════════════════ */}
      <section>
        <div className="flex items-baseline justify-between mb-1">
          <h2 className="font-headline text-xl md:text-2xl font-bold text-on-surface">
            Intelligence Picks
          </h2>
          <Link
            href={`/match/${featured.slug}`}
            className="text-primary text-sm font-medium hover:underline"
          >
            View Model &rarr;
          </Link>
        </div>
        <p className="text-secondary text-sm mb-6">
          Top-rated captain candidates based on current venue fit.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {captainPicks.map((pick) => {
            const teamColor = getTeamColorClass(pick.team as TeamCode);
            return (
              <div
                key={pick.playerName}
                className="bg-surface-container-high rounded-2xl p-5 transition-transform duration-200 hover:translate-y-[-4px] hover:shadow-lg hover:shadow-primary/5"
              >
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="font-headline text-lg font-bold text-on-surface">
                      {pick.playerName}
                    </h3>
                    <div className="flex items-center gap-2 mt-1">
                      <span
                        className={`inline-block w-2.5 h-2.5 rounded-full ${teamColor}`}
                      />
                      <span className="text-[13px] text-secondary">
                        {pick.team as TeamCode} &middot; {pick.role}
                      </span>
                    </div>
                  </div>
                  <GradeBadge grade={pick.grade as Grade} size="md" />
                </div>

                <div className="border-t border-outline-variant/20 pt-3">
                  <span className="text-[11px] uppercase tracking-[0.12em] text-outline block mb-1">
                    Venue Fit
                  </span>
                  <p className="text-sm text-secondary leading-relaxed line-clamp-2">
                    {pick.reasoning}
                  </p>
                </div>

                <div className="mt-4 flex items-center justify-between">
                  <span className="text-[11px] uppercase tracking-[0.12em] text-outline">
                    Projected Pts
                  </span>
                  <span className="font-headline text-base font-bold text-primary">
                    {pick.projectedPoints}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          TWO-COLUMN: Upcoming Analytics + System Core
         ═══════════════════════════════════════════ */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* ── Left: Upcoming Analytics ── */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex items-baseline justify-between mb-1">
            <h2 className="font-headline text-xl md:text-2xl font-bold text-on-surface">
              Upcoming Analytics
            </h2>
            <span className="text-[11px] uppercase tracking-[0.12em] text-outline">
              IPL 2026
            </span>
          </div>

          <div className="space-y-3">
            {upcomingMatches.map((match) => {
              const t1Color = getTeamColorClass(match.team1);
              const t2Color = getTeamColorClass(match.team2);

              return (
                <Link
                  key={match.slug}
                  href={`/match/${match.slug}`}
                  className="block bg-surface-container rounded-2xl p-4 transition-colors hover:bg-surface-bright/10"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      {/* Overlapping team circles */}
                      <div className="relative flex-shrink-0 w-10 h-6">
                        <span
                          className={`absolute left-0 top-0 w-6 h-6 rounded-full ${t1Color} ring-2 ring-surface-container`}
                        />
                        <span
                          className={`absolute left-4 top-0 w-6 h-6 rounded-full ${t2Color} ring-2 ring-surface-container`}
                        />
                      </div>

                      <div>
                        <span className="font-headline text-base font-bold text-on-surface">
                          {match.team1}{" "}
                          <span className="font-light text-outline">vs</span>{" "}
                          {match.team2}
                        </span>
                        <p className="text-[13px] text-secondary mt-0.5">
                          {match.venue}
                        </p>
                      </div>
                    </div>

                    <div className="text-right flex-shrink-0">
                      <p className="text-[13px] font-medium text-on-surface-variant">
                        {match.date}
                      </p>
                      <p className="text-[11px] text-outline">{match.time}</p>
                    </div>
                  </div>

                  {/* Probability + confidence badges (if available) */}
                  {match.probability && (
                    <div className="mt-3 pt-3 border-t border-outline-variant/15 flex items-center gap-3">
                      <span className="text-[13px] font-semibold text-primary">
                        {match.probability}
                      </span>
                      {match.confidenceLabel && (
                        <span className="text-[11px] bg-primary/10 text-primary px-2.5 py-0.5 rounded-full font-medium">
                          {match.confidenceLabel}
                        </span>
                      )}
                    </div>
                  )}
                </Link>
              );
            })}
          </div>
        </div>

        {/* ── Right: System Core ── */}
        <div className="lg:col-span-5">
          <div className="bg-surface-container rounded-2xl p-6 space-y-6">
            {/* Header with icon */}
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                <svg
                  className="w-5 h-5 text-primary"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={1.5}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z"
                  />
                </svg>
              </div>
              <div>
                <h2 className="font-headline text-lg font-bold text-on-surface">
                  System Core
                </h2>
                <p className="text-sm text-secondary leading-relaxed mt-1">
                  MatchPrism leverages a proprietary neural network to process{" "}
                  <span className="text-primary font-medium">
                    15,000+ data points
                  </span>{" "}
                  per match, delivering real-time intelligence on venue dynamics,
                  player form, and match probability.
                </p>
              </div>
            </div>

            {/* Feature list */}
            <div className="space-y-3">
              {[
                {
                  title: "Venue Dynamics",
                  desc: "Pitch behavior, boundary dimensions, weather impact",
                },
                {
                  title: "Player Sentiment",
                  desc: "Recent form, venue record, match-up analysis",
                },
                {
                  title: "Model Confidence",
                  desc: "Probability calibration with historical accuracy",
                },
              ].map((feature) => (
                <div key={feature.title} className="flex items-start gap-3">
                  <div className="flex-shrink-0 mt-0.5">
                    <svg
                      className="w-4.5 h-4.5 text-grade-a"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={2}
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-on-surface">
                      {feature.title}
                    </p>
                    <p className="text-[13px] text-secondary">{feature.desc}</p>
                  </div>
                </div>
              ))}
            </div>

            {/* Platform state box */}
            <div className="bg-surface-container-high rounded-xl p-4 border border-outline-variant/20">
              <span className="text-[11px] uppercase tracking-[0.15em] text-outline block mb-2">
                Platform State
              </span>
              <div className="flex items-center gap-2">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-grade-aplus opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-grade-aplus" />
                </span>
                <span className="font-headline text-sm font-bold text-on-surface">
                  Model v4.2.1
                </span>
                <span className="text-[11px] text-grade-aplus font-medium">
                  Online
                </span>
              </div>
            </div>

            {/* Tagline */}
            <p className="text-center text-sm text-secondary italic">
              See every match through a data lens
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
