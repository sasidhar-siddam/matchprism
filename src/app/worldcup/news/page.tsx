import Link from "next/link";
import { getWCArticles, readingTime } from "@/lib/worldcup";

export const metadata = {
  title: "World Cup 2026 Analysis & Articles | MatchPrism",
  description: "Data-driven match recaps, previews and analysis from the 2026 FIFA World Cup.",
};

const CATEGORY_COLORS: Record<string, string> = {
  "Match Recap": "text-grade-aplus bg-grade-aplus/10",
  "Match Preview": "text-primary bg-primary/10",
  Analysis: "text-secondary bg-secondary/10",
};

export default function WorldCupNewsPage() {
  const articles = getWCArticles();

  return (
    <div className="space-y-8 pb-12 max-w-3xl mx-auto">
      <header className="pt-4">
        <Link href="/worldcup" className="text-primary text-sm font-medium hover:underline">
          &larr; World Cup Hub
        </Link>
        <h1 className="font-headline text-2xl md:text-3xl font-bold text-on-surface mt-3">
          Analysis &amp; Articles
        </h1>
        <p className="text-secondary text-sm mt-1">
          Match intelligence from the MatchPrism editorial model.
        </p>
      </header>

      {articles.length === 0 && (
        <p className="text-sm text-secondary">
          No articles yet — run{" "}
          <code className="text-primary">python scripts/worldcup_generate_articles.py</code>.
        </p>
      )}

      {/* Featured lead article — larger treatment breaks the uniform grid */}
      {articles.length > 0 && (
        <Link
          href={`/worldcup/news/${articles[0].slug}`}
          className="block bg-surface-container-high rounded-2xl p-8 transition-colors hover:bg-surface-bright/10 group"
        >
          <div className="flex items-center gap-3 mb-4">
            <span className="text-[11px] font-semibold uppercase tracking-[0.12em] px-2.5 py-1 rounded-full text-primary bg-primary/10">
              {articles[0].category}
            </span>
            <span className="text-[11px] text-outline uppercase tracking-[0.12em]">
              {new Date(articles[0].publishedAt).toLocaleDateString("en-GB", {
                day: "numeric",
                month: "short",
              })}{" "}
              &middot; {readingTime(articles[0])} min read
            </span>
          </div>
          <h2 className="font-headline text-2xl md:text-3xl font-black text-on-surface group-hover:text-primary transition-colors leading-tight">
            {articles[0].title}
          </h2>
          <p className="text-base text-secondary leading-relaxed mt-3">{articles[0].dek}</p>
          {articles[0].keyStats.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-5">
              {articles[0].keyStats.slice(0, 3).map((s) => (
                <span
                  key={s.label}
                  className="text-[13px] bg-surface-container rounded-full px-3.5 py-1.5 text-on-surface-variant"
                >
                  {s.label}: <span className="font-semibold text-primary">{s.value}</span>
                </span>
              ))}
            </div>
          )}
        </Link>
      )}

      <div className="space-y-5">
        {articles.slice(1).map((a) => (
          <Link
            key={a.slug}
            href={`/worldcup/news/${a.slug}`}
            className="block bg-surface-container rounded-2xl p-6 transition-colors hover:bg-surface-container-high group"
          >
            <div className="flex items-center gap-3 mb-3">
              <span
                className={`text-[11px] font-semibold uppercase tracking-[0.12em] px-2.5 py-1 rounded-full ${CATEGORY_COLORS[a.category] ?? "text-secondary bg-secondary/10"}`}
              >
                {a.category}
              </span>
              <span className="text-[11px] text-outline uppercase tracking-[0.12em]">
                {new Date(a.publishedAt).toLocaleDateString("en-GB", {
                  day: "numeric",
                  month: "short",
                })}{" "}
                &middot; {readingTime(a)} min read
              </span>
            </div>
            <h2 className="font-headline text-xl md:text-2xl font-bold text-on-surface group-hover:text-primary transition-colors leading-snug">
              {a.title}
            </h2>
            <p className="text-sm text-secondary leading-relaxed mt-2">{a.dek}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
