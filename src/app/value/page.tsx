import Link from "next/link";
import { getOdds, getSchedule } from "@/lib/data";
import { getTeam } from "@/lib/teams";
import type { TeamCode } from "@/lib/types";
import {
  decimalToImplied,
  decimalToFractional,
  calcEdge,
  quarterKelly,
  getVerdict,
  expectedValue,
} from "@/lib/odds";

/* ---------- Metadata ---------- */

export const metadata = {
  title: "Value Finder | MatchPrism",
  description:
    "Where our model disagrees with the market. Tournament winner and match-level value analysis powered by historical data.",
};

/* ---------- Helpers ---------- */

function verdictBadge(verdict: "VALUE" | "FAIR" | "AVOID") {
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

function formatPct(n: number, decimals = 1): string {
  return `${n.toFixed(decimals)}%`;
}

/* ---------- Page ---------- */

export default function ValuePage() {
  const odds = getOdds();
  const schedule = getSchedule();

  // Sort tournament entries by edge (best value first)
  const tournamentEntries = odds.tournamentWinner
    .map((entry) => {
      const implied = decimalToImplied(entry.decimalOdds);
      const edge = calcEdge(entry.modelTitleProb, implied);
      const verdict = getVerdict(edge);
      const kelly = quarterKelly(entry.modelTitleProb, entry.decimalOdds);
      const ev = expectedValue(entry.modelTitleProb, entry.decimalOdds);
      const team = getTeam(entry.team);
      return { ...entry, implied, edge, verdict, kelly, ev, teamMeta: team };
    })
    .sort((a, b) => b.edge - a.edge);

  // Featured pick: highest positive edge
  const featured = tournamentEntries[0];

  // Match value: merge schedule with odds
  const matchValue = schedule
    .map((m) => {
      const matchOdds = odds.matchOdds[m.slug];
      if (!matchOdds) return null;

      const implied1 = decimalToImplied(matchOdds.team1Odds);
      const implied2 = decimalToImplied(matchOdds.team2Odds);
      const edge1 = calcEdge(m.team1WinProb, implied1);
      const edge2 = calcEdge(m.team2WinProb, implied2);
      const bestEdge = Math.max(edge1, edge2);
      const bestTeam = edge1 >= edge2 ? m.team1 : m.team2;
      const bestVerdict = getVerdict(bestEdge);

      return {
        ...m,
        matchOdds,
        implied1,
        implied2,
        edge1,
        edge2,
        bestEdge,
        bestTeam,
        bestVerdict,
      };
    })
    .filter(Boolean)
    .sort((a, b) => b!.bestEdge - a!.bestEdge);

  const valueCount = tournamentEntries.filter((e) => e.verdict === "VALUE").length;
  const hasMatchOdds = matchValue.length > 0;

  return (
    <main className="max-w-4xl mx-auto px-4 md:px-6 pt-24 pb-32 space-y-8">
      {/* ============================================================
          HERO
          ============================================================ */}
      <section className="space-y-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-grade-aplus/15 flex items-center justify-center">
            <svg
              className="w-5 h-5 text-grade-aplus"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941"
              />
            </svg>
          </div>
          <div>
            <h1 className="font-headline font-black text-2xl md:text-3xl text-on-surface">
              Value Finder
            </h1>
            <p className="text-[13px] text-on-surface-variant">
              Where our model disagrees with the market
            </p>
          </div>
        </div>

        <div className="bg-surface-container rounded-2xl p-4 space-y-2">
          <p className="text-[14px] text-on-surface-variant leading-relaxed">
            Value exists when the probability our model assigns to an outcome is
            <span className="text-on-surface font-medium"> higher </span>
            than what the bookmaker odds imply. A positive edge means the market
            may be underpricing that outcome based on historical data.
          </p>
          <div className="flex items-center gap-4 text-[12px]">
            <span className="text-grade-aplus font-bold">
              {valueCount} value {valueCount === 1 ? "pick" : "picks"} found
            </span>
            <span className="text-on-surface-variant/60">
              Updated {new Date(odds.lastUpdated).toLocaleDateString("en-GB", {
                day: "numeric",
                month: "short",
                year: "numeric",
              })}
            </span>
          </div>
        </div>
      </section>

      {/* ============================================================
          NO-VALUE CALLOUT (when market is efficient)
          ============================================================ */}
      {valueCount === 0 && (
        <section className="bg-surface-container-lowest rounded-2xl p-5 md:p-6 space-y-3 border border-grade-b/20">
          <div className="flex items-center gap-3">
            <span className="text-[11px] uppercase tracking-widest font-headline font-bold px-3 py-1 rounded-full bg-grade-b/15 text-grade-b">
              Market Looks Efficient
            </span>
          </div>
          <h2 className="font-headline font-black text-lg text-on-surface">
            No strong value signals in the tournament winner market right now
          </h2>
          <p className="text-[14px] text-on-surface-variant leading-relaxed">
            Our model and the bookmaker odds are closely aligned across all 10
            teams. The biggest edge we see is{" "}
            <span className="text-on-surface font-bold">
              {featured.teamMeta.code} +{featured.edge.toFixed(1)}%
            </span>
            , which is below our{" "}
            <span className="text-on-surface font-bold">+3% VALUE threshold</span>.
            When the model and the market disagree by this little, the smart
            move is usually to wait for a bigger edge.
          </p>
          <p className="text-[13px] text-on-surface-variant/70 leading-relaxed">
            This is the tool working as intended — stopping you from taking
            marginal bets just because the odds look tempting.
          </p>
        </section>
      )}

      {/* ============================================================
          FEATURED PICK (only if there's a real VALUE signal)
          ============================================================ */}
      {featured && featured.verdict === "VALUE" && (
        <section className="bg-surface-container-lowest rounded-2xl p-5 md:p-6 space-y-5 border border-grade-aplus/20">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div className="flex items-center gap-3">
              <span
                className="text-[11px] uppercase tracking-widest font-headline font-bold px-3 py-1 rounded-full bg-grade-aplus/15 text-grade-aplus"
              >
                Top Value Pick
              </span>
              <h2 className="font-headline font-black text-xl text-on-surface">
                <span style={{ color: featured.teamMeta.color }}>
                  {featured.teamMeta.code}
                </span>{" "}
                to Win IPL 2026
              </h2>
            </div>
            <span className="font-headline font-black text-2xl text-grade-aplus">
              {decimalToFractional(featured.decimalOdds)}
            </span>
          </div>

          {/* Key numbers */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              {
                label: "Market Implied",
                value: formatPct(featured.implied),
                sub: `at ${featured.decimalOdds.toFixed(2)}`,
              },
              {
                label: "Our Model",
                value: formatPct(featured.modelTitleProb),
                sub: "title probability",
              },
              {
                label: "Edge",
                value: `+${formatPct(featured.edge)}`,
                sub: "model advantage",
                highlight: true,
              },
              {
                label: "Quarter-Kelly",
                value: formatPct(featured.kelly * 100),
                sub: "of bankroll",
              },
            ].map((stat) => (
              <div
                key={stat.label}
                className="bg-surface-container rounded-xl p-3 space-y-1"
              >
                <span className="text-[11px] uppercase tracking-widest text-on-surface-variant font-headline font-bold">
                  {stat.label}
                </span>
                <p
                  className={`text-[18px] font-headline font-black ${
                    stat.highlight ? "text-grade-aplus" : "text-on-surface"
                  }`}
                >
                  {stat.value}
                </p>
                <span className="text-[11px] text-on-surface-variant/60">
                  {stat.sub}
                </span>
              </div>
            ))}
          </div>

          {/* Record */}
          <div className="flex items-center gap-4 text-[13px]">
            <span className="text-on-surface-variant">Current record:</span>
            <span className="font-bold text-on-surface">
              {featured.record.won}W-{featured.record.lost}L
            </span>
            <span className="text-on-surface-variant">
              {featured.record.points} pts
            </span>
            <span className="text-on-surface-variant">
              NRR {featured.record.nrr > 0 ? "+" : ""}
              {featured.record.nrr.toFixed(2)}
            </span>
          </div>

          {/* Model reasoning */}
          <div className="space-y-2">
            <h3 className="text-[11px] uppercase tracking-widest text-on-surface-variant font-headline font-bold">
              Why the Model Disagrees with the Market
            </h3>
            <p className="text-[14px] text-on-surface-variant leading-relaxed">
              {featured.reasoning}
            </p>
          </div>

          {/* EV callout */}
          <div className="bg-grade-aplus/5 rounded-xl p-3 flex items-center gap-3">
            <svg
              className="w-5 h-5 text-grade-aplus shrink-0"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <p className="text-[13px] text-on-surface leading-relaxed">
              <span className="font-bold">Expected value:</span>{" "}
              {featured.ev > 0 ? "+" : ""}
              {(featured.ev * 100).toFixed(0)}p per £1 staked.
              {" "}For every £1 the model suggests this bet is worth{" "}
              <span className="text-grade-aplus font-bold">
                £{(1 + featured.ev).toFixed(2)}
              </span>{" "}
              in the long run.
            </p>
          </div>
        </section>
      )}

      {/* ============================================================
          TOURNAMENT WINNER TABLE
          ============================================================ */}
      <section className="bg-surface-container-lowest rounded-2xl p-5 md:p-6 space-y-5">
        <h2 className="font-headline font-black text-xl text-on-surface">
          IPL 2026 Winner — Full Market
        </h2>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-white/5">
                {[
                  "Team",
                  "Record",
                  "NRR",
                  "Odds",
                  "Implied",
                  "Model",
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
              {tournamentEntries.map((entry) => {
                const isValue = entry.verdict === "VALUE";
                return (
                  <tr
                    key={entry.team}
                    className={`border-b border-white/5 last:border-0 ${
                      isValue ? "bg-grade-aplus/5" : ""
                    }`}
                  >
                    <td className="py-3 pr-4">
                      <span
                        className="text-[14px] font-headline font-bold"
                        style={{ color: entry.teamMeta.color }}
                      >
                        {entry.teamMeta.code}
                      </span>
                    </td>
                    <td className="py-3 pr-4 text-[13px] text-on-surface-variant whitespace-nowrap">
                      {entry.record.won}-{entry.record.lost}
                      {entry.record.noResult ? `-${entry.record.noResult}NR` : ""}
                    </td>
                    <td
                      className={`py-3 pr-4 text-[13px] font-medium whitespace-nowrap ${
                        entry.record.nrr >= 0.5
                          ? "text-grade-aplus"
                          : entry.record.nrr <= -1
                          ? "text-grade-d"
                          : "text-on-surface-variant"
                      }`}
                    >
                      {entry.record.nrr > 0 ? "+" : ""}
                      {entry.record.nrr.toFixed(2)}
                    </td>
                    <td className="py-3 pr-4 text-[14px] text-on-surface font-medium">
                      {decimalToFractional(entry.decimalOdds)}
                    </td>
                    <td className="py-3 pr-4 text-[13px] text-on-surface-variant">
                      {formatPct(entry.implied)}
                    </td>
                    <td className="py-3 pr-4 text-[14px] text-on-surface font-medium">
                      {formatPct(entry.modelTitleProb, 0)}
                    </td>
                    <td
                      className={`py-3 pr-4 text-[14px] font-bold ${
                        entry.edge > 0 ? "text-grade-aplus" : entry.edge < -2 ? "text-grade-d" : "text-on-surface-variant"
                      }`}
                    >
                      {entry.edge > 0 ? "+" : ""}
                      {formatPct(entry.edge)}
                    </td>
                    <td className="py-3">{verdictBadge(entry.verdict)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <p className="text-[11px] text-on-surface-variant/60 leading-relaxed">
          Overround: {odds.overround.toFixed(1)}%. Source: {odds.source}.
          Model probabilities sum to 100% (no overround).
        </p>
      </section>

      {/* ============================================================
          MATCH-LEVEL VALUE
          ============================================================ */}
      <section className="bg-surface-container-lowest rounded-2xl p-5 md:p-6 space-y-5">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <h2 className="font-headline font-black text-xl text-on-surface">
            Match-Level Value
          </h2>
          <Link
            href="/matches"
            className="text-[12px] font-headline font-bold text-primary hover:text-primary-container transition-colors"
          >
            View all matches
          </Link>
        </div>

        {!hasMatchOdds && (
          <div className="bg-surface-container rounded-xl p-4">
            <p className="text-[13px] text-on-surface-variant leading-relaxed">
              Match-level odds are not currently available. Tournament-winner
              value is the focus of today&apos;s analysis — see the table above.
              Individual match previews with model probabilities are available
              on the <Link href="/matches" className="text-primary hover:underline">matches page</Link>.
            </p>
          </div>
        )}

        <div className="space-y-3">
          {matchValue.map((m) => {
            if (!m) return null;
            const t1 = getTeam(m.team1);
            const t2 = getTeam(m.team2);
            return (
              <Link
                key={m.slug}
                href={`/match/${m.slug}`}
                className="block bg-surface-container rounded-xl p-4 hover:bg-surface-container-high transition-colors"
              >
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2 text-[14px] font-headline font-bold">
                      <span style={{ color: t1.color }}>{t1.code}</span>
                      <span className="text-on-surface-variant text-[12px]">vs</span>
                      <span style={{ color: t2.color }}>{t2.code}</span>
                    </div>
                    <span className="text-[12px] text-on-surface-variant">
                      {m.date}
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    {m.bestEdge > 0 && (
                      <span className="text-[12px] font-bold text-grade-aplus">
                        {m.bestTeam} +{formatPct(m.bestEdge)} edge
                      </span>
                    )}
                    {verdictBadge(m.bestVerdict)}
                  </div>
                </div>
                <div className="mt-2 grid grid-cols-2 gap-4 text-[12px] text-on-surface-variant">
                  <div>
                    <span style={{ color: t1.color }} className="font-bold">
                      {t1.code}
                    </span>
                    : Model {m.team1WinProb}% vs Book{" "}
                    {formatPct(m.implied1)}
                    {m.edge1 > 0 && (
                      <span className="text-grade-aplus font-bold">
                        {" "}(+{formatPct(m.edge1)})
                      </span>
                    )}
                  </div>
                  <div>
                    <span style={{ color: t2.color }} className="font-bold">
                      {t2.code}
                    </span>
                    : Model {m.team2WinProb}% vs Book{" "}
                    {formatPct(m.implied2)}
                    {m.edge2 > 0 && (
                      <span className="text-grade-aplus font-bold">
                        {" "}(+{formatPct(m.edge2)})
                      </span>
                    )}
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      </section>

      {/* ============================================================
          HOW IT WORKS
          ============================================================ */}
      <section className="space-y-4">
        <h2 className="font-headline font-black text-xl text-on-surface">
          How It Works
        </h2>

        <div className="grid md:grid-cols-3 gap-3">
          {[
            {
              title: "1. Model Probability",
              body: "We compute win probabilities from 6,847 T20 matches using venue stats, squad strength, head-to-head records, and player-venue fit grades. No AI, no gut feel — pure historical data.",
            },
            {
              title: "2. Implied Probability",
              body: "Bookmaker odds translate directly to implied probability. Odds of 40/1 imply a 2.4% chance. We strip the overround to compare apples-to-apples with our model.",
            },
            {
              title: "3. Edge & Value",
              body: "When our model says 8% and the market says 2.4%, the edge is +5.6%. Value exists when the market underprices an outcome. Quarter-Kelly sizing manages risk.",
            },
          ].map((card) => (
            <div
              key={card.title}
              className="bg-surface-container rounded-2xl p-4 space-y-2"
            >
              <h3 className="text-[14px] font-headline font-bold text-on-surface">
                {card.title}
              </h3>
              <p className="text-[13px] text-on-surface-variant leading-relaxed">
                {card.body}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ============================================================
          DISCLAIMER
          ============================================================ */}
      <section className="bg-surface-container rounded-2xl p-4 space-y-2">
        <h3 className="text-[11px] uppercase tracking-widest text-on-surface-variant font-headline font-bold">
          Important
        </h3>
        <p className="text-[12px] text-on-surface-variant/60 leading-relaxed">
          This analysis is for informational and educational purposes only. It
          is not financial or betting advice. Model probabilities are derived
          from historical data and may not reflect current conditions, injuries,
          or team changes. Odds are indicative and may differ from what is
          currently available. Past performance does not guarantee future
          results. Always exercise independent judgment and only stake what you
          can afford to lose. If you or someone you know has a gambling problem,
          contact the National Gambling Helpline at 1-800-522-4700.
        </p>
      </section>
    </main>
  );
}
