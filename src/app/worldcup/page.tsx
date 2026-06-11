import Link from "next/link";
import {
  getWCSchedule,
  getWCDigest,
  getWCNews,
  getWCArticles,
  getUpcomingWCMatches,
  getWCGroupTables,
} from "@/lib/worldcup";
import { Countdown } from "@/components/Countdown";
import { LocalTime } from "@/components/LocalTime";

export const metadata = {
  title: "World Cup 2026 Intelligence | MatchPrism",
  description:
    "Data-driven World Cup 2026 coverage: fixtures, group standings, daily analysis and curated headlines.",
};

export default function WorldCupPage() {
  const schedule = getWCSchedule();
  const digest = getWCDigest();
  const news = getWCNews();
  const articles = getWCArticles();

  if (!schedule) {
    return (
      <div className="py-20 text-center">
        <h1 className="font-headline text-2xl font-bold text-on-surface mb-2">
          World Cup 2026
        </h1>
        <p className="text-sm text-secondary">
          Fixture data not generated yet. Run{" "}
          <code className="text-primary">python scripts/worldcup_fetch_fixtures.py</code>.
        </p>
      </div>
    );
  }

  const upcoming = getUpcomingWCMatches(schedule, 9);
  const featured = upcoming[0];
  const groupTables = getWCGroupTables(schedule);
  const previewBySlug = new Map(
    (digest?.matchPreviews ?? []).map((p) => [p.slug, p]),
  );
  const recentResults = schedule.matches
    .filter((m) => m.status === "played")
    .slice(-6)
    .reverse();

  return (
    <div className="space-y-10 pb-12">
      {/* ═══ HERO — Next Match ═══ */}
      <section className="relative -mx-4 md:-mx-8 -mt-4 overflow-hidden">
        <div
          className="absolute inset-0"
          style={{
            background:
              "linear-gradient(135deg, var(--color-surface-container-low) 0%, var(--color-surface) 40%, var(--color-surface-container-low) 70%, var(--color-surface) 100%)",
          }}
        />
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage:
              "linear-gradient(var(--color-on-surface) 1px, transparent 1px), linear-gradient(90deg, var(--color-on-surface) 1px, transparent 1px)",
            backgroundSize: "40px 40px",
          }}
        />

        <div className="relative z-10 flex flex-col items-center py-14 px-4 md:py-20">
          <div className="flex items-center gap-2 mb-4">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary-container opacity-75" />
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-primary-container" />
            </span>
            <span className="text-[11px] font-semibold tracking-[0.15em] uppercase text-primary">
              FIFA World Cup 2026
            </span>
          </div>

          {featured ? (
            <>
              <p className="text-secondary text-sm tracking-wide mb-6">
                {featured.venue}
                {featured.group ? ` · ${featured.group}` : ` · ${featured.stage}`}
              </p>

              <div className="flex flex-col sm:flex-row items-center gap-2 sm:gap-6 mb-8 text-center">
                <span className="font-headline text-3xl md:text-5xl font-black tracking-tight text-on-surface">
                  {featured.homeTeam}
                </span>
                <span className="font-headline text-2xl md:text-4xl font-light text-outline">
                  vs
                </span>
                <span className="font-headline text-3xl md:text-5xl font-black tracking-tight text-on-surface">
                  {featured.awayTeam}
                </span>
              </div>

              <Countdown targetDate={featured.dateRaw} targetTime={featured.time} />

              <p className="mt-5 text-[13px] text-outline">
                {featured.date} &middot; {featured.time}{" "}
                <LocalTime date={featured.dateRaw} time={featured.time} />
              </p>
            </>
          ) : (
            <p className="text-secondary text-sm">Tournament complete.</p>
          )}

          <Link
            href="/worldcup/matches"
            className="mt-6 inline-flex items-center gap-2 bg-primary/10 hover:bg-primary/20 text-primary text-sm font-semibold px-6 py-2.5 rounded-full transition-colors"
          >
            Full Fixture List
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </Link>
        </div>
      </section>

      {/* ═══ DAILY BRIEF ═══ */}
      {digest && (
        <section className="bg-surface-container rounded-2xl p-6">
          <div className="flex items-baseline justify-between mb-3">
            <h2 className="font-headline text-xl font-bold text-on-surface">
              Daily Brief
            </h2>
            <span className="text-[11px] uppercase tracking-[0.12em] text-outline">
              Updated {new Date(digest.generatedAt).toLocaleDateString("en-GB", { day: "numeric", month: "short" })}
            </span>
          </div>
          <p className="text-sm text-secondary leading-relaxed">{digest.dailyBrief}</p>
        </section>
      )}

      {/* ═══ MATCH PREVIEWS ═══ */}
      {digest && digest.matchPreviews.length > 0 && (
        <section>
          <h2 className="font-headline text-xl md:text-2xl font-bold text-on-surface mb-1">
            Match Intelligence
          </h2>
          <p className="text-secondary text-sm mb-6">
            Analytical previews for the next fixtures.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {digest.matchPreviews.map((p) => (
              <div
                key={p.slug}
                className="bg-surface-container-high rounded-2xl p-5 transition-transform duration-200 hover:translate-y-[-4px] hover:shadow-lg hover:shadow-primary/5"
              >
                <span className="text-[11px] uppercase tracking-[0.12em] text-outline block mb-2">
                  Match {p.matchNumber}
                </span>
                <h3 className="font-headline text-base font-bold text-on-surface mb-2">
                  {p.headline}
                </h3>
                <p className="text-[13px] text-secondary leading-relaxed mb-3">
                  {p.preview}
                </p>
                <div className="border-t border-outline-variant/20 pt-3">
                  <span className="text-[11px] uppercase tracking-[0.12em] text-primary block mb-1">
                    Key Fact
                  </span>
                  <p className="text-[13px] text-secondary leading-relaxed">{p.keyFact}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ═══ TWO-COLUMN: Upcoming + Headlines ═══ */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Upcoming fixtures */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex items-baseline justify-between mb-1">
            <h2 className="font-headline text-xl md:text-2xl font-bold text-on-surface">
              Upcoming Fixtures
            </h2>
            <Link href="/worldcup/matches" className="text-primary text-sm font-medium hover:underline">
              All 104 &rarr;
            </Link>
          </div>

          <div className="space-y-3">
            {upcoming.map((m) => {
              const preview = previewBySlug.get(m.slug);
              return (
                <div key={m.slug} className="bg-surface-container rounded-2xl p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="font-headline text-base font-bold text-on-surface">
                        {m.homeTeam} <span className="font-light text-outline">vs</span>{" "}
                        {m.awayTeam}
                      </span>
                      <p className="text-[13px] text-secondary mt-0.5">
                        {m.venue}
                        {m.group ? ` · ${m.group}` : ` · ${m.stage}`}
                      </p>
                    </div>
                    <div className="text-right flex-shrink-0">
                      <p className="text-[13px] font-medium text-on-surface-variant">{m.date}</p>
                      <p className="text-[11px] text-outline">{m.time}</p>
                    </div>
                  </div>
                  {preview && (
                    <p className="mt-3 pt-3 border-t border-outline-variant/15 text-[13px] text-secondary leading-relaxed line-clamp-2">
                      {preview.preview}
                    </p>
                  )}
                </div>
              );
            })}
          </div>

          {/* Recent results */}
          {recentResults.length > 0 && (
            <>
              <h2 className="font-headline text-xl font-bold text-on-surface pt-4">
                Latest Results
              </h2>
              <div className="space-y-3">
                {recentResults.map((m) => (
                  <div key={m.slug} className="bg-surface-container rounded-2xl p-4 flex items-center justify-between">
                    <span className="font-headline text-base font-bold text-on-surface">
                      {m.homeTeam}{" "}
                      <span className="text-primary">{m.homeScore}–{m.awayScore}</span>{" "}
                      {m.awayTeam}
                    </span>
                    <span className="text-[11px] uppercase tracking-[0.12em] text-outline">
                      {m.group ?? m.stage}
                    </span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>

        {/* Headlines */}
        <div className="lg:col-span-5 space-y-6">
          {articles.length > 0 && (
            <div className="bg-surface-container rounded-2xl p-6">
              <div className="flex items-baseline justify-between mb-4">
                <h2 className="font-headline text-lg font-bold text-on-surface">
                  Intelligence Desk
                </h2>
                <Link href="/worldcup/news" className="text-primary text-sm font-medium hover:underline">
                  All articles &rarr;
                </Link>
              </div>
              <div className="space-y-4">
                {articles.slice(0, 3).map((a) => (
                  <Link key={a.slug} href={`/worldcup/news/${a.slug}`} className="block group py-1">
                    <span className="text-[11px] font-semibold uppercase tracking-[0.12em] text-primary">
                      {a.category}
                    </span>
                    <p className="text-sm font-semibold text-on-surface group-hover:text-primary transition-colors leading-snug mt-1">
                      {a.title}
                    </p>
                  </Link>
                ))}
              </div>
            </div>
          )}

          <div className="bg-surface-container rounded-2xl p-6">
            <div className="flex items-baseline justify-between mb-4">
              <h2 className="font-headline text-lg font-bold text-on-surface">
                Top Stories
              </h2>
              {news && (
                <span className="text-[11px] uppercase tracking-[0.12em] text-outline">
                  {new Date(news.fetchedAt).toLocaleDateString("en-GB", { day: "numeric", month: "short" })}
                </span>
              )}
            </div>
            <div className="space-y-4">
              {(digest?.topStories?.length ? digest.topStories : (news?.items ?? []).slice(0, 6)).map(
                (story) => (
                  <a
                    key={story.url}
                    href={story.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block group py-1"
                  >
                    <p className="text-sm font-semibold text-on-surface group-hover:text-primary transition-colors leading-snug">
                      {story.title}
                    </p>
                    <p className="text-[11px] text-outline mt-1 uppercase tracking-[0.12em]">
                      {story.source}
                    </p>
                  </a>
                ),
              )}
              {!news && !digest && (
                <p className="text-sm text-secondary">
                  No headlines yet — run the news pipeline.
                </p>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* ═══ GROUP TABLES ═══ */}
      <section>
        <h2 className="font-headline text-xl md:text-2xl font-bold text-on-surface mb-1">
          Group Standings
        </h2>
        <p className="text-secondary text-sm mb-6">
          Live tables computed from completed group-stage fixtures.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(groupTables).map(([group, rows]) => (
            <div key={group} className="bg-surface-container rounded-2xl p-4">
              <h3 className="font-headline text-sm font-bold text-primary uppercase tracking-[0.12em] mb-3">
                {group}
              </h3>
              <table className="w-full text-[13px]">
                <thead>
                  <tr className="text-[11px] uppercase tracking-[0.1em] text-outline">
                    <th className="text-left font-medium pb-2">Team</th>
                    <th className="text-center font-medium pb-2 w-8">P</th>
                    <th className="text-center font-medium pb-2 w-8">GD</th>
                    <th className="text-center font-medium pb-2 w-8">Pts</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r, i) => (
                    <tr key={r.team} className={i < 2 ? "text-on-surface" : "text-secondary"}>
                      <td className="py-1.5 font-medium">{r.team}</td>
                      <td className="text-center">{r.played}</td>
                      <td className="text-center">
                        {r.goalDiff > 0 ? `+${r.goalDiff}` : r.goalDiff}
                      </td>
                      <td className="text-center font-bold text-primary">{r.points}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
