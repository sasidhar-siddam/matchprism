import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getPlayer, getAllPlayerSlugs, getPlayerTeamMap, nameToSlug } from "@/lib/data";
import { getTeam } from "@/lib/teams";
import { GradeBadge } from "@/components/GradeBadge";
import type { Grade } from "@/lib/types";

/* ── Static Params ── */
export function generateStaticParams() {
  const slugs = getAllPlayerSlugs();
  return slugs.map((slug) => ({ slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const player = getPlayer(slug);
  const name = player?.name ?? "Player";
  return {
    title: `${name} | Player Intelligence | MatchPrism`,
    description: `In-depth venue analytics, form analysis, and performance intelligence for ${name}. Data-driven insights powered by MatchPrism.`,
  };
}

/* ── Radar Chart Helpers (visual filler — hardcoded until multi-dimensional stats are computed) ── */
const radarAxes = [
  { label: "Power", angle: -90 },
  { label: "Spin", angle: -30 },
  { label: "Consistency", angle: 30 },
  { label: "Pace", angle: 90 },
  { label: "Defense", angle: 150 },
  { label: "Strike", angle: 210 },
];

const radarValues = [0.78, 0.65, 0.92, 0.7, 0.85, 0.88];
const radarRadius = 100;
const radarCenter = { x: 140, y: 130 };

function polarToCartesian(angle: number, radius: number) {
  const rad = (angle * Math.PI) / 180;
  return {
    x: radarCenter.x + radius * Math.cos(rad),
    y: radarCenter.y + radius * Math.sin(rad),
  };
}

function getPolygonPoints(values: number[]): string {
  return values
    .map((v, i) => {
      const { x, y } = polarToCartesian(radarAxes[i].angle, v * radarRadius);
      return `${x},${y}`;
    })
    .join(" ");
}

function getHexagonPoints(radiusFraction: number): string {
  return radarAxes
    .map((axis) => {
      const { x, y } = polarToCartesian(
        axis.angle,
        radarRadius * radiusFraction
      );
      return `${x},${y}`;
    })
    .join(" ");
}

/* ── Label positioning ── */
function getLabelPosition(angle: number) {
  const { x, y } = polarToCartesian(angle, radarRadius + 22);
  let anchor: "start" | "middle" | "end" = "middle";
  const dx = 0;
  if (angle > 0 && angle < 180) anchor = "start";
  if (angle > 180 || angle < 0) {
    if (angle === -90) anchor = "middle";
    else if (angle === -30) anchor = "start";
    else anchor = "end";
  }
  if (angle === 90) anchor = "start";
  if (angle === -90) anchor = "middle";
  if (angle === 150) anchor = "end";
  if (angle === 210) anchor = "end";
  if (angle === -30) anchor = "start";
  if (angle === 30) anchor = "start";
  return { x, y, anchor, dx };
}

/* ── Helpers ── */
function inferRole(player: Record<string, unknown>): string {
  const overall = player.overall as { batting?: { innings?: number }; bowling?: { innings?: number } } | undefined;
  const batInnings = overall?.batting?.innings ?? 0;
  const bowlInnings = overall?.bowling?.innings ?? 0;
  if (bowlInnings > 0 && batInnings > 0) {
    const ratio = bowlInnings / batInnings;
    if (ratio > 0.7) return "All-rounder";
  }
  if (bowlInnings > batInnings) return "Bowler";
  return "Batter";
}

function getFirstGradedVenue(
  venues: Record<string, { grade?: string }> | undefined
): { name: string; grade: string } | null {
  if (!venues) return null;
  for (const [name, data] of Object.entries(venues)) {
    if (data.grade && data.grade !== "N/A") {
      return { name, grade: data.grade };
    }
  }
  return null;
}

const VALID_GRADES = new Set(["A+", "A", "B", "C", "D"]);

function toGrade(raw: string | undefined): Grade {
  if (raw && VALID_GRADES.has(raw)) return raw as Grade;
  return "C";
}

/* ── Page Component ── */
export default async function PlayerProfilePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const player = getPlayer(slug);
  if (!player) return notFound();

  // Resolve team code from match data
  const teamMap = getPlayerTeamMap();
  const teamCode = teamMap[player.name] ?? "";
  const teamMeta = getTeam(teamCode);

  const batting = player.overall?.batting ?? {};
  const bowling = player.overall?.bowling;
  const role = inferRole(player);
  const innings = batting.innings ?? 0;
  const careerRuns = batting.runs ?? 0;
  const highestScore = batting.highestScore ?? "-";
  const careerAvg = batting.average ?? 0;
  const careerSR = batting.strikeRate ?? 0;
  const fifties = batting.fifties ?? 0;
  const hundreds = batting.hundreds ?? 0;
  const fours = batting.fours ?? 0;
  const sixes = batting.sixes ?? 0;

  // Grade from first venue with a valid grade
  const gradedVenue = getFirstGradedVenue(player.venues);
  const grade = toGrade(gradedVenue?.grade);

  // Venue stats for performance table (use first graded venue)
  const venueData = gradedVenue ? player.venues[gradedVenue.name] : null;
  const venueBatting = venueData?.batting;
  const venueAvg = venueBatting?.average ?? 0;
  const venueSR = venueBatting?.strikeRate ?? 0;
  const venueRuns = venueBatting?.runs ?? 0;
  const venueFifties = venueBatting?.fifties ?? 0;
  const venueHundreds = venueBatting?.hundreds ?? 0;
  const venueFours = venueBatting?.fours ?? 0;
  const venueSixes = venueBatting?.sixes ?? 0;

  // Compute deltas (percentage difference from career)
  const avgDelta =
    careerAvg > 0
      ? (((venueAvg - careerAvg) / careerAvg) * 100).toFixed(1)
      : "--";
  const srDelta =
    careerSR > 0
      ? (((venueSR - careerSR) / careerSR) * 100).toFixed(1)
      : "--";

  // Recent form bar chart: use last 10 formTimeline entries
  const formTimeline: Array<{ date: string; runs: number; venue: string }> =
    player.formTimeline ?? [];
  const recentScores = formTimeline.slice(0, 10).reverse(); // oldest to newest
  const maxScore = Math.max(...recentScores.map((s: { runs: number }) => s.runs), 1);

  // Recent form summary
  const recentForm = player.recentForm;

  // Season stats — may contain batting and/or bowling fields
  const seasonStats: Record<
    string,
    {
      innings?: number;
      runs?: number;
      average?: number;
      strikeRate?: number;
      bowlInnings?: number;
      bowlWickets?: number;
      bowlEconomy?: number;
      bowlAverage?: number;
    }
  > = player.seasonStats ?? {};

  // Venue names for the selector dropdown
  const venueNames = Object.keys(player.venues ?? {}).filter(
    (v) => player.venues[v].grade && player.venues[v].grade !== "N/A"
  );

  // Neural insight text — generated from real data
  const recentFormData = recentForm?.last10;
  const insightText = recentFormData
    ? `Averaging ${recentFormData.average.toFixed(1)} in the last ${recentFormData.innings} innings with a strike rate of ${recentFormData.strikeRate.toFixed(1)}. ${
        recentForm.trend === "improving"
          ? "Form trending upward."
          : recentForm.trend === "declining"
            ? "Form trending downward."
            : "Form remains consistent."
      }`
    : `Career average of ${careerAvg.toFixed(1)} across ${innings} innings.`;

  return (
    <div className="py-8 md:py-12 space-y-10">
      {/* ══════════════════════════════════════════════════════
          SECTION 1 — Player Header
         ══════════════════════════════════════════════════════ */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left: Photo + Identity */}
        <div className="lg:col-span-8 flex flex-col sm:flex-row gap-8 items-start">
          {/* Photo placeholder with prism glow */}
          <div className="relative shrink-0">
            <div className="absolute -inset-1 bg-gradient-to-tr from-primary-container to-primary rounded-3xl blur opacity-60" />
            <div className="relative w-48 h-64 rounded-3xl bg-surface-container flex items-end justify-center overflow-hidden">
              <svg
                className="w-32 h-40 text-outline-variant/40"
                viewBox="0 0 64 80"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                aria-hidden="true"
              >
                <circle cx="32" cy="22" r="14" fill="currentColor" />
                <ellipse cx="32" cy="68" rx="24" ry="18" fill="currentColor" />
              </svg>
            </div>
          </div>

          {/* Identity block */}
          <div className="flex flex-col gap-3">
            <span className="inline-flex items-center gap-1.5 text-[11px] font-headline font-bold uppercase tracking-[0.2em] text-primary-container">
              <span className="w-1.5 h-1.5 rounded-full bg-primary-container" />
              Pro Intelligence
            </span>
            <h1 className="text-5xl md:text-7xl font-headline font-black leading-[1.05] tracking-tight text-on-surface">
              {player.name}
            </h1>
            <div className="flex items-center gap-3 mt-1">
              {teamCode && (
                <>
                  <span
                    className="w-3 h-3 rounded-full shrink-0"
                    style={{ backgroundColor: teamMeta.color }}
                  />
                  <span className="text-base text-on-surface-variant font-body">
                    {teamMeta.name}
                  </span>
                  <span className="text-outline">|</span>
                </>
              )}
              <span className="text-base text-on-surface-variant font-body">
                {role}
              </span>
            </div>
            <div className="flex flex-wrap gap-3 mt-3">
              <span className="text-[13px] font-body text-on-surface-variant bg-surface-container rounded-full px-4 py-1.5">
                {innings} Innings
              </span>
              <span className="text-[13px] font-body text-on-surface-variant bg-surface-container rounded-full px-4 py-1.5">
                {careerRuns.toLocaleString()} Career Runs
              </span>
              <span className="text-[13px] font-body text-on-surface-variant bg-surface-container rounded-full px-4 py-1.5">
                HS: {highestScore}
              </span>
            </div>
          </div>
        </div>

        {/* Right: Grade card */}
        <div className="lg:col-span-4">
          <div className="bg-surface-container rounded-3xl p-8 flex flex-col items-center gap-5">
            <span className="text-[11px] font-headline font-bold uppercase tracking-[0.2em] text-on-surface-variant">
              Venue Intelligence Grade
            </span>
            <GradeBadge grade={grade} size="xl" />
            {gradedVenue && (
              <span className="text-[12px] text-on-surface-variant font-body text-center">
                {gradedVenue.name}
              </span>
            )}
            <div className="w-full flex flex-col items-center gap-1 mt-2">
              <span className="text-[11px] font-headline font-bold uppercase tracking-[0.2em] text-on-surface-variant">
                Career Average
              </span>
              <span className="text-3xl font-headline font-black text-on-surface">
                {careerAvg.toFixed(1)}
              </span>
            </div>
            {/* Prism gauge bar */}
            <div className="w-full h-[2px] rounded-full bg-gradient-to-r from-primary-container via-primary to-primary-container mt-2" />
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════════════════════
          SECTION 2 — Insights Grid
         ══════════════════════════════════════════════════════ */}
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2/3: Recent Form Pulse */}
        <div className="lg:col-span-2 bg-surface-container rounded-3xl p-6 md:p-8">
          <h2 className="text-xl font-headline font-bold text-on-surface mb-6">
            Recent Form Pulse
          </h2>
          {recentScores.length > 0 ? (
            <>
              <div className="flex items-end gap-2 h-[140px]">
                {recentScores.map((score: { runs: number; venue: string }, i: number) => {
                  const heightPx = maxScore > 0 ? (score.runs / maxScore) * 130 : 0;
                  return (
                    <div
                      key={i}
                      className="flex-1 flex flex-col items-center justify-end gap-1 group relative"
                    >
                      {/* Tooltip */}
                      <div className="absolute -top-7 left-1/2 -translate-x-1/2 bg-surface-container-highest text-on-surface text-[11px] font-body px-2 py-0.5 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">
                        {score.runs} runs
                      </div>
                      <div
                        className="w-full bg-primary-container/20 rounded-t-lg transition-colors hover:bg-primary-container/40"
                        style={{ height: `${Math.max(heightPx, 4)}px` }}
                      />
                    </div>
                  );
                })}
              </div>
              {/* Labels row */}
              <div className="flex gap-2 mt-3">
                {recentScores.map((score: { runs: number; venue: string }, i: number) => (
                  <div
                    key={i}
                    className="flex-1 text-center text-[11px] text-on-surface-variant font-body truncate"
                  >
                    {i === 0
                      ? "Oldest"
                      : i === recentScores.length - 1
                        ? "Latest"
                        : ""}
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="text-on-surface-variant font-body text-sm">
              No recent form data available.
            </p>
          )}
        </div>

        {/* Right 1/3: Neural Insight */}
        <div className="lg:col-span-1">
          <div className="bg-primary/10 border border-primary/10 rounded-2xl p-6 md:p-8 h-full flex flex-col gap-4">
            {/* Icon */}
            <div className="w-10 h-10 rounded-xl bg-primary/20 flex items-center justify-center">
              <svg
                className="w-5 h-5 text-primary"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <path d="M12 2L2 7l10 5 10-5-10-5Z" />
                <path d="M2 17l10 5 10-5" />
                <path d="M2 12l10 5 10-5" />
              </svg>
            </div>
            <h3 className="text-sm font-headline font-bold uppercase tracking-[0.15em] text-primary">
              Neural Insight
            </h3>
            <p className="text-base text-on-surface font-body leading-relaxed">
              &ldquo;{insightText}&rdquo;
            </p>
            <p className="text-[12px] text-on-surface-variant font-body mt-auto">
              Generated from {innings} career innings
            </p>
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════════════════════
          SECTION 3 — Radar & Stats
         ══════════════════════════════════════════════════════ */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Venue Fit Analysis (Radar) */}
        <div className="lg:col-span-4 bg-surface-container rounded-3xl p-6 md:p-8">
          <h2 className="text-xl font-headline font-bold text-on-surface mb-2">
            Venue Fit Analysis
          </h2>
          {/* Venue selector */}
          <div className="mb-6">
            <select
              className="w-full bg-surface-container-high text-on-surface text-sm font-body rounded-xl px-4 py-2.5 border border-outline-variant/20 focus:outline-none focus:border-primary-container appearance-none cursor-pointer"
              defaultValue={gradedVenue?.name ?? ""}
              aria-label="Select venue for analysis"
            >
              {venueNames.map((v) => (
                <option key={v} value={v}>
                  {v}
                </option>
              ))}
            </select>
          </div>

          {/* Radar SVG */}
          <div className="relative w-full flex items-center justify-center">
            <svg
              viewBox="0 0 280 260"
              className="w-full max-w-[280px]"
              aria-label="Radar chart showing venue fit across six performance dimensions"
              role="img"
            >
              {/* Concentric hexagons */}
              {[1, 0.66, 0.33].map((scale) => (
                <polygon
                  key={scale}
                  points={getHexagonPoints(scale)}
                  fill="none"
                  stroke="var(--color-outline-variant)"
                  strokeWidth="1"
                  strokeDasharray="4 3"
                  opacity="0.5"
                />
              ))}

              {/* Axis lines */}
              {radarAxes.map((axis) => {
                const { x, y } = polarToCartesian(axis.angle, radarRadius);
                return (
                  <line
                    key={axis.label}
                    x1={radarCenter.x}
                    y1={radarCenter.y}
                    x2={x}
                    y2={y}
                    stroke="var(--color-outline-variant)"
                    strokeWidth="0.5"
                    opacity="0.4"
                  />
                );
              })}

              {/* Data polygon */}
              <polygon
                points={getPolygonPoints(radarValues)}
                fill="var(--color-primary)"
                fillOpacity="0.15"
                stroke="var(--color-primary)"
                strokeWidth="2"
              />

              {/* Data points */}
              {radarValues.map((v, i) => {
                const { x, y } = polarToCartesian(
                  radarAxes[i].angle,
                  v * radarRadius
                );
                return (
                  <circle
                    key={i}
                    cx={x}
                    cy={y}
                    r="3"
                    fill="var(--color-primary)"
                  />
                );
              })}

              {/* Axis labels */}
              {radarAxes.map((axis) => {
                const pos = getLabelPosition(axis.angle);
                return (
                  <text
                    key={axis.label}
                    x={pos.x}
                    y={pos.y}
                    textAnchor={pos.anchor}
                    className="fill-on-surface-variant"
                    style={{ fontSize: "11px", fontFamily: "var(--font-body)" }}
                  >
                    {axis.label}
                  </text>
                );
              })}
            </svg>
          </div>
        </div>

        {/* Right: Aggregated Performance */}
        <div className="lg:col-span-8 bg-surface-container rounded-3xl p-6 md:p-8">
          <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
            <h2 className="text-xl font-headline font-bold text-on-surface">
              Aggregated Performance
            </h2>
            {/* Format toggle */}
            <div className="flex gap-1 bg-surface-container-high rounded-xl p-1">
              <button
                className="px-4 py-1.5 text-[13px] font-headline font-bold rounded-lg bg-primary-container text-on-primary transition-colors"
                aria-pressed="true"
              >
                T20
              </button>
              <button
                className="px-4 py-1.5 text-[13px] font-headline font-bold rounded-lg text-on-surface-variant hover:text-on-surface transition-colors"
                aria-pressed="false"
              >
                ODI
              </button>
            </div>
          </div>

          {/* Stats table */}
          <div className="overflow-x-auto">
            <table
              className="w-full text-left"
              aria-label="Player aggregated performance statistics"
            >
              <thead>
                <tr className="border-b border-outline-variant/20">
                  <th className="pb-3 text-[12px] font-headline font-bold uppercase tracking-[0.15em] text-on-surface-variant">
                    Metric
                  </th>
                  <th className="pb-3 text-[12px] font-headline font-bold uppercase tracking-[0.15em] text-primary-container text-right">
                    Projected (Venue)
                  </th>
                  <th className="pb-3 text-[12px] font-headline font-bold uppercase tracking-[0.15em] text-on-surface-variant text-right">
                    Career
                  </th>
                  <th className="pb-3 text-[12px] font-headline font-bold uppercase tracking-[0.15em] text-on-surface-variant text-right">
                    Delta
                  </th>
                </tr>
              </thead>
              <tbody className="text-sm font-body">
                <tr className="border-b border-outline-variant/10">
                  <td className="py-4 text-on-surface">Batting Average</td>
                  <td className="py-4 text-right font-headline font-bold text-primary-container">
                    {venueAvg.toFixed(2)}
                  </td>
                  <td className="py-4 text-right text-on-surface-variant">
                    {careerAvg.toFixed(2)}
                  </td>
                  <td
                    className={`py-4 text-right font-bold ${
                      avgDelta !== "--" && parseFloat(avgDelta) >= 0
                        ? "text-grade-aplus"
                        : "text-on-surface-variant"
                    }`}
                  >
                    {avgDelta !== "--" ? `${parseFloat(avgDelta) >= 0 ? "+" : ""}${avgDelta}%` : "--"}
                  </td>
                </tr>
                <tr className="border-b border-outline-variant/10">
                  <td className="py-4 text-on-surface">Strike Rate</td>
                  <td className="py-4 text-right font-headline font-bold text-primary-container">
                    {venueSR.toFixed(2)}
                  </td>
                  <td className="py-4 text-right text-on-surface-variant">
                    {careerSR.toFixed(2)}
                  </td>
                  <td
                    className={`py-4 text-right font-bold ${
                      srDelta !== "--" && parseFloat(srDelta) >= 0
                        ? "text-grade-aplus"
                        : "text-on-surface-variant"
                    }`}
                  >
                    {srDelta !== "--" ? `${parseFloat(srDelta) >= 0 ? "+" : ""}${srDelta}%` : "--"}
                  </td>
                </tr>
                <tr className="border-b border-outline-variant/10">
                  <td className="py-4 text-on-surface">Total Runs</td>
                  <td className="py-4 text-right font-headline font-bold text-primary-container">
                    {venueRuns.toLocaleString()}
                  </td>
                  <td className="py-4 text-right text-on-surface-variant">
                    {careerRuns.toLocaleString()}
                  </td>
                  <td className="py-4 text-right text-grade-aplus font-bold">
                    <span aria-label="Trending upward">&#9650;</span>
                  </td>
                </tr>
                <tr className="border-b border-outline-variant/10">
                  <td className="py-4 text-on-surface">100s / 50s</td>
                  <td className="py-4 text-right font-headline font-bold text-primary-container">
                    {venueHundreds} / {venueFifties}
                  </td>
                  <td className="py-4 text-right text-on-surface-variant">
                    {hundreds} / {fifties}
                  </td>
                  <td className="py-4 text-right text-on-surface-variant">
                    --
                  </td>
                </tr>
                <tr>
                  <td className="py-4 text-on-surface">Boundaries 4s / 6s</td>
                  <td className="py-4 text-right font-headline font-bold text-primary-container">
                    {venueFours} / {venueSixes}
                  </td>
                  <td className="py-4 text-right text-on-surface-variant">
                    {fours} / {sixes}
                  </td>
                  <td className="py-4 text-right text-on-surface-variant">
                    --
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Season comparison */}
          {Object.keys(seasonStats).length > 0 && (
            <div className="mt-8">
              <h3 className="text-sm font-headline font-bold uppercase tracking-[0.15em] text-on-surface-variant mb-4">
                Season Comparison
              </h3>
              <div className="overflow-x-auto">
                <table
                  className="w-full text-left"
                  aria-label="Season-by-season performance comparison"
                >
                  <thead>
                    <tr className="border-b border-outline-variant/20">
                      <th className="pb-3 text-[12px] font-headline font-bold uppercase tracking-[0.15em] text-on-surface-variant">
                        Season
                      </th>
                      <th className="pb-3 text-[12px] font-headline font-bold uppercase tracking-[0.15em] text-on-surface-variant text-right">
                        Innings
                      </th>
                      <th className="pb-3 text-[12px] font-headline font-bold uppercase tracking-[0.15em] text-on-surface-variant text-right">
                        Runs
                      </th>
                      <th className="pb-3 text-[12px] font-headline font-bold uppercase tracking-[0.15em] text-on-surface-variant text-right">
                        Average
                      </th>
                      <th className="pb-3 text-[12px] font-headline font-bold uppercase tracking-[0.15em] text-on-surface-variant text-right">
                        Strike Rate
                      </th>
                    </tr>
                  </thead>
                  <tbody className="text-sm font-body">
                    {Object.entries(seasonStats)
                      .sort(([a], [b]) => b.localeCompare(a))
                      .map(([season, stats]) => (
                        <tr
                          key={season}
                          className="border-b border-outline-variant/10"
                        >
                          <td className="py-3 text-on-surface font-headline font-bold">
                            {season}
                          </td>
                          <td className="py-3 text-right text-on-surface-variant">
                            {stats.innings ?? stats.bowlInnings ?? "-"}
                          </td>
                          <td className="py-3 text-right text-on-surface-variant">
                            {stats.runs != null ? stats.runs : stats.bowlWickets != null ? `${stats.bowlWickets}w` : "-"}
                          </td>
                          <td className="py-3 text-right text-on-surface-variant">
                            {stats.average != null ? stats.average.toFixed(2) : stats.bowlAverage != null ? stats.bowlAverage.toFixed(2) : "-"}
                          </td>
                          <td className="py-3 text-right text-on-surface-variant">
                            {stats.strikeRate != null ? stats.strikeRate.toFixed(2) : stats.bowlEconomy != null ? `${stats.bowlEconomy.toFixed(2)} econ` : "-"}
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* ══════════════════════════════════════════════════════
          SECTION 4 — Action Buttons
         ══════════════════════════════════════════════════════ */}
      <section className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
        <button
          className="bg-gradient-to-br from-primary-container to-[#00d1ff] text-on-primary font-headline font-bold text-sm uppercase tracking-widest rounded-full px-8 py-4 hover:opacity-90 transition-opacity min-h-[44px] min-w-[44px]"
          type="button"
        >
          Share Intelligence Analysis
        </button>
        <button
          className="bg-surface-container-high border border-outline-variant/20 text-on-surface font-headline font-bold text-sm uppercase tracking-widest rounded-full px-8 py-4 hover:bg-surface-container-highest transition-colors min-h-[44px] min-w-[44px]"
          type="button"
        >
          Export Stats (PDF)
        </button>
      </section>
    </div>
  );
}
