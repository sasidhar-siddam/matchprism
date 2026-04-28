import Link from "next/link";
import { notFound } from "next/navigation";
import { getMatch, getAllMatchSlugs, getPitchReport, nameToSlug } from "@/lib/data";
import type { AdvancedAnalysisRow, Grade } from "@/lib/types";
import { getTeam } from "@/lib/teams";
import { GradeBadge } from "@/components/GradeBadge";

/* ---------- Static params ---------- */

export function generateStaticParams() {
  return getAllMatchSlugs().map((slug) => ({ slug }));
}

/* ---------- Metadata ---------- */

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const match = getMatch(slug);
  if (!match) return { title: "Match Not Found | MatchPrism" };
  const t1 = getTeam(match.team1);
  const t2 = getTeam(match.team2);
  return {
    title: `${t1.code} vs ${t2.code} Preview | MatchPrism`,
    description: `Data-driven match preview for ${t1.name} vs ${t2.name} at ${match.venue.name}. Win probability, venue intelligence, captain picks, and advanced analysis.`,
  };
}

/* ---------- Helpers ---------- */

function gradeTextColor(grade: Grade): string {
  const map: Record<Grade, string> = {
    "A+": "text-grade-aplus",
    A: "text-grade-a",
    B: "text-grade-b",
    C: "text-grade-c",
    D: "text-grade-d",
  };
  return map[grade];
}

function verdictBadge(verdict: AdvancedAnalysisRow["verdict"]) {
  const styles: Record<string, string> = {
    VALUE: "bg-grade-aplus/15 text-grade-aplus",
    FAIR: "bg-grade-b/15 text-grade-b",
    AVOID: "bg-grade-d/15 text-grade-d",
  };
  return (
    <span
      className={`inline-block text-[11px] font-headline font-bold px-2.5 py-0.5 rounded-full ${styles[verdict]}`}
    >
      {verdict}
    </span>
  );
}

/* ---------- SVG Icons ---------- */

function IconBrain() {
  return (
    <svg
      className="w-5 h-5 text-primary-container"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={1.5}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714a2.25 2.25 0 00.659 1.591L19 14.5m-4.75-11.396c.251.023.501.05.75.082M12 3v5.714"
      />
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M3.75 21h16.5M4.5 18.75h15M5.25 16.5h13.5"
      />
    </svg>
  );
}

function IconWarning() {
  return (
    <svg
      className="w-5 h-5 shrink-0"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
      />
    </svg>
  );
}

function IconChevron() {
  return (
    <svg
      className="w-5 h-5 shrink-0 transition-transform duration-200 group-open:rotate-180"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M19.5 8.25l-7.5 7.5-7.5-7.5"
      />
    </svg>
  );
}

function IconVenue() {
  return (
    <svg
      className="w-4 h-4 text-on-surface-variant"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={1.5}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z"
      />
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z"
      />
    </svg>
  );
}

function IconCalendar() {
  return (
    <svg
      className="w-4 h-4 text-on-surface-variant"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={1.5}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5"
      />
    </svg>
  );
}

function IconClock() {
  return (
    <svg
      className="w-4 h-4 text-on-surface-variant"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={1.5}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
  );
}

/* ---------- Page Component ---------- */

export default async function MatchPreviewPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const match = getMatch(slug);
  if (!match) notFound();
  const pitchReport = getPitchReport(slug);

  const t1 = getTeam(match.team1);
  const t2 = getTeam(match.team2);
  const venue = match.venue;

  return (
    <div className="space-y-8 py-6">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-[11px] text-on-surface-variant">
        <Link href="/" className="hover:text-primary transition-colors">
          Home
        </Link>
        <span>/</span>
        <span className="text-on-surface">
          {t1.code} vs {t2.code}
        </span>
      </nav>

      {/* ============================================================
          SECTION 1: Match Header + Win Probability
          ============================================================ */}
      <section className="space-y-6">
        {/* Team names with accent bars */}
        <div className="flex items-center justify-center gap-4">
          <div
            className="w-2 h-8 rounded-full"
            style={{ backgroundColor: t1.color }}
          />
          <h1 className="font-headline font-black text-3xl md:text-4xl text-on-surface tracking-tight">
            {t1.code} vs {t2.code}
          </h1>
          <div
            className="w-2 h-8 rounded-full"
            style={{ backgroundColor: t2.color }}
          />
        </div>

        {/* Meta row */}
        <div className="flex flex-wrap items-center justify-center gap-4 text-[13px] text-on-surface-variant">
          <span className="flex items-center gap-1.5">
            <IconVenue />
            {venue.name}, {venue.city}
          </span>
          <span className="flex items-center gap-1.5">
            <IconCalendar />
            {match.date}
          </span>
          <span className="flex items-center gap-1.5">
            <IconClock />
            {match.time}
          </span>
        </div>

        {/* Model Confidence */}
        <div className="bg-surface-container-lowest rounded-2xl p-6 text-center space-y-1">
          <p className="text-[11px] uppercase tracking-widest text-on-surface-variant font-headline font-bold">
            Model Confidence
          </p>
          <p className="text-5xl font-headline font-black text-primary">
            {match.modelConfidence}%
          </p>
        </div>

        {/* Win probability bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-[13px] font-headline font-bold">
            <span style={{ color: t1.color }}>
              {t1.code} {match.team1WinProb}%
            </span>
            <span style={{ color: t2.color }}>
              {match.team2WinProb}% {t2.code}
            </span>
          </div>
          <div className="flex h-3 rounded-full overflow-hidden gap-0.5">
            <div
              className="rounded-l-full transition-all"
              style={{
                width: `${match.team1WinProb}%`,
                backgroundColor: t1.color,
              }}
            />
            <div
              className="rounded-r-full transition-all"
              style={{
                width: `${match.team2WinProb}%`,
                backgroundColor: t2.color,
              }}
            />
          </div>
        </div>
      </section>

      {/* ============================================================
          SECTION 2: Venue Intelligence (Bento Grid)
          ============================================================ */}
      <section className="space-y-4">
        <h2 className="font-headline font-black text-xl text-on-surface">
          Venue Intelligence
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Left 2/3 */}
          <div className="md:col-span-2 space-y-4">
            {/* 4 Metric Cards */}
            <div className="grid grid-cols-2 gap-3">
              {[
                {
                  label: "Avg 1st Innings",
                  value: venue.avg1stInnings.toString(),
                },
                {
                  label: "Chase Win %",
                  value: `${venue.chaseWinPct}%`,
                },
                { label: "Toss Choice", value: "BOWL" },
                { label: "Pitch Nature", value: "PACE" },
              ].map((m) => (
                <div
                  key={m.label}
                  className="bg-surface-container rounded-2xl p-4 space-y-1"
                >
                  <p className="text-[11px] uppercase tracking-widest text-on-surface-variant font-headline font-bold">
                    {m.label}
                  </p>
                  <p className="text-2xl font-headline font-black text-on-surface">
                    {m.value}
                  </p>
                </div>
              ))}
            </div>

            {/* Venue Verdict */}
            <div className="border-l-4 border-primary-container bg-surface-container rounded-r-2xl p-4 space-y-1">
              <p className="text-[11px] uppercase tracking-widest text-primary-container font-headline font-bold">
                Venue Verdict
              </p>
              <p className="text-[14px] text-on-surface-variant leading-relaxed">
                {venue.verdict}
              </p>
            </div>
          </div>

          {/* Right 1/3: Wicket Intelligence */}
          <div className="bg-surface-container rounded-2xl p-5 space-y-5">
            <h3 className="text-[11px] uppercase tracking-widest text-on-surface-variant font-headline font-bold">
              Wicket Intelligence
            </h3>

            {/* Pace Utility */}
            <div className="space-y-2">
              <div className="flex justify-between text-[13px]">
                <span className="text-on-surface-variant">Pace Utility</span>
                <span className="font-headline font-bold text-on-surface">
                  {Math.round(venue.paceWicketPct)}%
                </span>
              </div>
              <div className="h-2 bg-surface-container-lowest rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary rounded-full transition-all"
                  style={{ width: `${venue.paceWicketPct}%` }}
                />
              </div>
            </div>

            {/* Spin Grip */}
            <div className="space-y-2">
              <div className="flex justify-between text-[13px]">
                <span className="text-on-surface-variant">Spin Grip</span>
                <span className="font-headline font-bold text-on-surface">
                  {Math.round(venue.spinWicketPct)}%
                </span>
              </div>
              <div className="h-2 bg-surface-container-lowest rounded-full overflow-hidden">
                <div
                  className="h-full bg-secondary rounded-full transition-all"
                  style={{ width: `${venue.spinWicketPct}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================
          SECTION 2.5: Conditions Intelligence (Pitch Scanner)
          ============================================================ */}
      {pitchReport && (
        <section className="space-y-4">
          {/* Header */}
          <div className="flex items-center gap-2">
            <svg
              className="w-5 h-5 text-primary-container"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M2.25 15a4.5 4.5 0 004.5 4.5H18a3.75 3.75 0 001.332-7.257 3 3 0 00-3.758-3.848 5.25 5.25 0 00-10.233 2.33A4.502 4.502 0 002.25 15z"
              />
            </svg>
            <h2 className="font-headline font-black text-xl text-on-surface">
              Conditions Intelligence
            </h2>
          </div>

          {/* Three-column grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Card 1: Dew Analysis */}
            <div className="bg-surface-container rounded-2xl p-5 space-y-3">
              <p className="text-[11px] uppercase tracking-widest text-on-surface-variant font-headline font-bold">
                Dew Analysis
              </p>
              <p className="text-4xl font-headline font-black text-primary">
                {pitchReport.dewAnalysis.probability}%
              </p>
              <p className="text-[11px] text-on-surface-variant uppercase tracking-wider">
                Dew Probability
              </p>
              <span
                className={`inline-block text-[11px] font-headline font-bold px-2.5 py-0.5 rounded-full ${
                  pitchReport.dewAnalysis.impact === "Heavy"
                    ? "bg-grade-aplus/15 text-grade-aplus"
                    : pitchReport.dewAnalysis.impact === "Moderate"
                      ? "bg-grade-b/15 text-grade-b"
                      : "bg-secondary/15 text-secondary"
                }`}
              >
                {pitchReport.dewAnalysis.impact}
              </span>
              {pitchReport.dewAnalysis.secondInningsAdvantage && (
                <p className="text-[13px] text-on-surface-variant">
                  Advantage: Chasing Team
                </p>
              )}
            </div>

            {/* Card 2: Bowling Conditions */}
            <div className="bg-surface-container rounded-2xl p-5 space-y-4">
              <p className="text-[11px] uppercase tracking-widest text-on-surface-variant font-headline font-bold">
                Bowling Conditions
              </p>

              {/* Swing Potential */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-[13px]">
                  <span className="text-on-surface-variant">Swing Potential</span>
                  <span className="font-headline font-bold text-on-surface">
                    {pitchReport.pitchBehavior.swingPotential}%
                  </span>
                </div>
                <div className="h-1.5 bg-surface-container-lowest rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary rounded-full transition-all"
                    style={{ width: `${pitchReport.pitchBehavior.swingPotential}%` }}
                  />
                </div>
              </div>

              {/* Spin Potential */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-[13px]">
                  <span className="text-on-surface-variant">Spin Potential</span>
                  <span className="font-headline font-bold text-on-surface">
                    {pitchReport.pitchBehavior.spinPotential}%
                  </span>
                </div>
                <div className="h-1.5 bg-surface-container-lowest rounded-full overflow-hidden">
                  <div
                    className="h-full bg-secondary rounded-full transition-all"
                    style={{ width: `${pitchReport.pitchBehavior.spinPotential}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Card 3: Match Day Weather */}
            <div className="bg-surface-container rounded-2xl p-5 space-y-3">
              <p className="text-[11px] uppercase tracking-widest text-on-surface-variant font-headline font-bold">
                Match Day Weather
              </p>
              <div className="space-y-2 text-[14px]">
                <div className="flex justify-between">
                  <span className="text-on-surface-variant">Temperature</span>
                  <span className="font-headline font-bold text-on-surface">
                    {pitchReport.weather.temperature}&deg;C
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-on-surface-variant">Humidity</span>
                  <span className="font-headline font-bold text-on-surface">
                    {pitchReport.weather.humidity}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-on-surface-variant">Wind</span>
                  <span className="font-headline font-bold text-on-surface">
                    {pitchReport.weather.windSpeed} km/h
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-on-surface-variant">Cloud Cover</span>
                  <span className="font-headline font-bold text-on-surface">
                    {pitchReport.weather.cloudCover}%
                  </span>
                </div>
              </div>
              <p className="text-[13px] text-on-surface-variant">
                {pitchReport.weather.description}
                {pitchReport.weatherSource === "estimated" && (
                  <span className="text-[11px] text-on-surface-variant/60 ml-1">
                    (estimated)
                  </span>
                )}
              </p>
            </div>
          </div>

          {/* Toss Intelligence Bar */}
          <div className="bg-surface-container-lowest rounded-2xl p-5">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
              <div>
                <p className="text-[11px] uppercase tracking-widest text-on-surface-variant font-headline font-bold">
                  Toss Recommendation
                </p>
                <p className="text-[16px] font-headline font-bold text-on-surface mt-1">
                  {pitchReport.tossIntelligence.recommendation}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-[14px] text-on-surface-variant">
                  Bowl First{" "}
                  <span className="font-headline font-bold text-on-surface">
                    {pitchReport.tossIntelligence.bowlFirstProbability}%
                  </span>
                </span>
                <span className="inline-block text-[11px] font-headline font-bold px-2.5 py-0.5 rounded-full bg-primary-container/15 text-primary-container">
                  {pitchReport.tossIntelligence.confidence}% confidence
                </span>
              </div>
            </div>
            {pitchReport.reasoning.length > 0 && (
              <ul className="mt-3 space-y-1">
                {pitchReport.reasoning.map((reason, i) => (
                  <li
                    key={i}
                    className="text-[13px] text-on-surface-variant leading-relaxed"
                  >
                    {reason}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>
      )}

      {/* ============================================================
          SECTION 3: Captain Genius Picks
          ============================================================ */}
      <section className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-2">
            <IconBrain />
            <h2 className="font-headline font-black text-xl text-on-surface">
              Captain Genius Picks
            </h2>
          </div>
          <span className="text-[11px] uppercase tracking-widest font-headline font-bold text-primary-container bg-primary-container/10 px-3 py-1 rounded-full">
            Live Optimization
          </span>
        </div>

        {/* Pick Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {match.captainPicks.map((pick) => (
            <div
              key={pick.playerName}
              className="bg-surface-container rounded-2xl p-5 space-y-4"
            >
              <div className="flex items-start gap-3">
                {/* Player photo placeholder */}
                <div className="bg-surface-container-highest w-16 h-16 rounded-2xl shrink-0" />
                <div className="space-y-1 min-w-0">
                  <GradeBadge grade={pick.grade as Grade} size="sm" />
                  <Link href={`/player/${nameToSlug(pick.playerName)}`} className="font-headline font-bold text-on-surface hover:text-primary transition-colors text-[15px] truncate block">
                    {pick.playerName}
                  </Link>
                  <p className="text-[11px] text-on-surface-variant uppercase tracking-wider">
                    {pick.role}
                  </p>
                </div>
              </div>

              {/* Last 5 scores */}
              <div className="space-y-1">
                <p className="text-[11px] text-on-surface-variant uppercase tracking-wider font-bold">
                  Last 5
                </p>
                <div className="flex gap-1.5">
                  {pick.last5.map((score, i) => (
                    <span
                      key={i}
                      className="w-7 h-7 flex items-center justify-center rounded-lg bg-surface-container-highest text-[11px] font-bold text-on-surface"
                    >
                      {score}
                    </span>
                  ))}
                </div>
              </div>

              {/* Reasoning */}
              <p className="text-[13px] text-on-surface-variant leading-relaxed">
                {pick.reasoning}
              </p>
            </div>
          ))}
        </div>

        {/* Avoid Today */}
        {match.avoidPicks.map((avoid) => (
          <div
            key={avoid.playerName}
            className="flex items-start gap-3 bg-error-container/10 border border-error/20 rounded-2xl p-4"
          >
            <div className="text-error mt-0.5">
              <IconWarning />
            </div>
            <div className="space-y-1">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-[11px] uppercase tracking-widest font-headline font-bold text-error">
                  Avoid Today
                </span>
                <span className="font-headline font-bold text-on-surface text-[14px]">
                  {avoid.playerName}
                </span>
                <GradeBadge grade={avoid.grade as Grade} size="sm" />
              </div>
              <p className="text-[13px] text-on-surface-variant leading-relaxed">
                {avoid.reason}
              </p>
            </div>
          </div>
        ))}
      </section>

      {/* ============================================================
          SECTION 4: Advanced Analysis
          ============================================================ */}
      <section className="bg-surface-container-lowest rounded-2xl p-5 md:p-6 space-y-5">
        <h2 className="font-headline font-black text-xl text-on-surface">
          Advanced Analysis
        </h2>

        {/* Toggle buttons */}
        <div className="flex gap-2">
          <button className="text-[11px] uppercase tracking-widest font-headline font-bold px-4 py-2 rounded-xl bg-primary-container text-on-primary transition-colors">
            Probability
          </button>
          <button className="text-[11px] uppercase tracking-widest font-headline font-bold px-4 py-2 rounded-xl bg-surface-container text-on-surface-variant hover:text-on-surface transition-colors">
            Simulation
          </button>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-white/5">
                {[
                  "Outcome",
                  "Model Prob.",
                  "Implied Prob.",
                  "Edge",
                  "Verdict",
                ].map((h) => (
                  <th
                    key={h}
                    className="text-[11px] uppercase tracking-widest text-on-surface-variant font-headline font-bold pb-3 pr-4"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {match.advancedAnalysis.map((row) => (
                <tr
                  key={row.outcome}
                  className="border-b border-white/5 last:border-0"
                >
                  <td className="py-3 pr-4 text-[14px] font-medium text-on-surface">
                    {row.outcome}
                  </td>
                  <td className="py-3 pr-4 text-[14px] text-on-surface-variant">
                    {row.modelProb}%
                  </td>
                  <td className="py-3 pr-4 text-[14px] text-on-surface-variant">
                    {row.impliedProb}%
                  </td>
                  <td
                    className={`py-3 pr-4 text-[14px] font-bold ${
                      row.edge > 0 ? "text-grade-aplus" : "text-grade-d"
                    }`}
                  >
                    {row.edge > 0 ? "+" : ""}
                    {row.edge}%
                  </td>
                  <td className="py-3">{verdictBadge(row.verdict)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Disclaimer */}
        <p className="text-[11px] text-on-surface-variant/60 leading-relaxed">
          Analysis is based on historical data and statistical models.
          Probabilities reflect model output and do not guarantee outcomes.
          Always exercise independent judgment.
        </p>
      </section>

      {/* ============================================================
          SECTION 5: Head to Head ("Historical Supremacy")
          ============================================================ */}
      <section className="space-y-4">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <h2 className="font-headline font-black text-xl text-on-surface">
            Historical Supremacy
          </h2>
          <div className="flex items-center gap-2 text-[14px] font-headline font-bold">
            <span style={{ color: t1.color }}>{t1.code}</span>
            <span className="text-on-surface">
              {match.h2h.team1Wins} - {match.h2h.team2Wins}
            </span>
            <span style={{ color: t2.color }}>{t2.code}</span>
          </div>
        </div>

        {/* Horizontally scrollable cards */}
        <div className="flex overflow-x-auto gap-3 pb-2 -mx-1 px-1 scrollbar-thin">
          {match.h2h.recentMatches.map((m, i) => {
            const isTeam1Winner = m.winner === match.team1;
            return (
              <div
                key={i}
                className="min-w-[280px] bg-surface-container rounded-2xl p-4 space-y-3 shrink-0"
              >
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-on-surface-variant">
                    {m.date}
                  </span>
                  <span className="text-[11px] text-on-surface-variant bg-surface-container-highest px-2 py-0.5 rounded-full">
                    {m.venue}
                  </span>
                </div>

                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span
                      className={`text-[14px] font-headline font-bold ${
                        m.winner === m.team1
                          ? "text-on-surface"
                          : "text-on-surface-variant"
                      }`}
                    >
                      {m.team1}
                    </span>
                    <span className="text-[14px] text-on-surface font-medium">
                      {m.team1Score}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span
                      className={`text-[14px] font-headline font-bold ${
                        m.winner === m.team2
                          ? "text-on-surface"
                          : "text-on-surface-variant"
                      }`}
                    >
                      {m.team2}
                    </span>
                    <span className="text-[14px] text-on-surface font-medium">
                      {m.team2Score}
                    </span>
                  </div>
                </div>

                <div
                  className="text-[11px] font-headline font-bold px-2.5 py-1 rounded-full inline-block"
                  style={{
                    backgroundColor: isTeam1Winner
                      ? `color-mix(in srgb, ${t1.color} 15%, transparent)`
                      : `color-mix(in srgb, ${t2.color} 15%, transparent)`,
                    color: isTeam1Winner ? t1.color : t2.color,
                  }}
                >
                  {m.margin}
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* ============================================================
          SECTION 6: Player Venue Fit
          ============================================================ */}
      <section className="space-y-4">
        <h2 className="font-headline font-black text-xl text-on-surface">
          Player Venue Fit
        </h2>

        {/* Tabs (server-rendered, both visible via CSS peer trick) */}
        <div>
          {/* Tab headers */}
          <div className="flex gap-6 border-b border-white/5">
            <div className="border-b-2 border-primary-container pb-3">
              <span className="text-[11px] uppercase tracking-widest font-headline font-bold text-primary-container">
                {t1.name.split(" ").pop()}
              </span>
            </div>
            <div className="pb-3">
              <span className="text-[11px] uppercase tracking-widest font-headline font-bold text-on-surface-variant">
                {t2.name.split(" ").pop()}
              </span>
            </div>
          </div>

          {/* Team 1 table (active) */}
          <div className="overflow-x-auto mt-4">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-white/5">
                  {["Player", "Role", "Venue Avg", "Venue SR/Econ", "Oracle Grade"].map(
                    (h) => (
                      <th
                        key={h}
                        className="text-[11px] uppercase tracking-widest text-on-surface-variant font-headline font-bold pb-3 pr-4"
                      >
                        {h}
                      </th>
                    )
                  )}
                </tr>
              </thead>
              <tbody>
                {match.playerFit.team1.map((player) => (
                  <tr
                    key={player.name}
                    className="border-b border-white/5 last:border-0"
                  >
                    <td className="py-3 pr-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-surface-container-highest shrink-0" />
                        <Link href={`/player/${nameToSlug(player.name)}`} className="text-[14px] font-medium text-on-surface hover:text-primary transition-colors">
                          {player.name}
                        </Link>
                      </div>
                    </td>
                    <td className="py-3 pr-4 text-[13px] text-on-surface-variant">
                      {player.role}
                    </td>
                    <td className="py-3 pr-4 text-[14px] text-on-surface font-medium">
                      {player.venueAvg}
                    </td>
                    <td className="py-3 pr-4 text-[14px] text-on-surface font-medium">
                      {player.venueEcon !== undefined
                        ? player.venueEcon
                        : player.venueSR}
                    </td>
                    <td className="py-3 pr-4">
                      <span
                        className={`font-headline font-bold text-[14px] ${gradeTextColor(
                          player.grade as Grade
                        )}`}
                      >
                        {player.grade}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* ============================================================
          SECTION 7: Intelligence Glossary (Accordion)
          ============================================================ */}
      <section className="space-y-3">
        <h2 className="font-headline font-black text-xl text-on-surface">
          Intelligence Glossary
        </h2>

        {[
          {
            title: "Understanding the Powerplay",
            content:
              "The first six overs of each innings are designated as the powerplay. During this phase, only two fielders are permitted outside the 30-yard circle. This restriction incentivizes aggressive batting and creates high-scoring phases. At venues like Chinnaswamy with short boundaries, powerplay runs per over tend to exceed the tournament average significantly. Our model weights powerplay performance heavily when projecting first-innings totals.",
          },
          {
            title: "Impact Player Rule",
            content:
              "IPL 2026 retains the impact player substitution rule, allowing teams to substitute one player at any point during the match. This tactical dimension adds strategic depth, as teams can bring in specialist batters during chases or additional bowlers to exploit conditions. Our model accounts for likely impact player usage patterns when calculating win probability and player projections.",
          },
          {
            title: "The Decision Review System (DRS)",
            content:
              "Each team receives two unsuccessful reviews per innings. The DRS allows teams to challenge on-field umpire decisions using ball-tracking technology (Hawk-Eye) and UltraEdge. Historically, DRS overturns approximately 28% of reviewed LBW decisions. Venue-specific factors like bounce and seam movement influence DRS success rates, which our model incorporates into bowling projections.",
          },
        ].map((item) => (
          <details
            key={item.title}
            className="group bg-surface-container rounded-2xl border border-white/5"
          >
            <summary className="flex items-center justify-between cursor-pointer p-4 select-none list-none [&::-webkit-details-marker]:hidden">
              <span className="font-headline font-bold text-[14px] text-on-surface">
                {item.title}
              </span>
              <IconChevron />
            </summary>
            <div className="px-4 pb-4">
              <p className="text-[13px] text-on-surface-variant leading-relaxed">
                {item.content}
              </p>
            </div>
          </details>
        ))}
      </section>
    </div>
  );
}
