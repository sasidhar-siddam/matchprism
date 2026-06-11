import Link from "next/link";
import { notFound } from "next/navigation";
import { getWCArticle, getWCArticles, readingTime } from "@/lib/worldcup";

export const dynamicParams = false;

export function generateStaticParams() {
  return getWCArticles().map((a) => ({ slug: a.slug }));
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const article = getWCArticle(slug);
  if (!article) return {};
  return {
    title: `${article.title} | MatchPrism`,
    description: article.dek,
  };
}

export default async function WorldCupArticlePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const article = getWCArticle(slug);
  if (!article) notFound();

  const published = new Date(article.publishedAt);

  return (
    <article className="max-w-3xl mx-auto pb-12">
      {/* ═══ Article header ═══ */}
      <header className="pt-4 mb-8">
        <Link
          href="/worldcup/news"
          className="text-primary text-sm font-medium hover:underline"
        >
          &larr; All Articles
        </Link>

        <div className="flex items-center gap-3 mt-5 mb-4">
          <span className="text-[11px] font-semibold uppercase tracking-[0.15em] text-primary bg-primary/10 px-2.5 py-1 rounded-full">
            {article.category}
          </span>
          <span className="text-[11px] text-outline uppercase tracking-[0.12em]">
            {published.toLocaleDateString("en-GB", {
              weekday: "long",
              day: "numeric",
              month: "long",
              year: "numeric",
            })}{" "}
            &middot; {readingTime(article)} min read
          </span>
        </div>

        <h1 className="font-headline text-3xl md:text-4xl font-black tracking-tight text-on-surface leading-tight">
          {article.title}
        </h1>
        <p className="text-base md:text-lg text-secondary leading-relaxed mt-4">
          {article.dek}
        </p>
        <p className="text-[11px] uppercase tracking-[0.12em] text-outline mt-4">
          MatchPrism Intelligence Desk &middot; model-written, editor-reviewed
        </p>
      </header>

      {/* ═══ Key stats strip (the data-driven hero) ═══ */}
      {article.keyStats.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8">
          {article.keyStats.map((s) => (
            <div key={s.label} className="bg-surface-container rounded-2xl p-4">
              <span className="text-[11px] uppercase tracking-[0.12em] text-outline block mb-1">
                {s.label}
              </span>
              <span className="font-headline text-base font-bold text-primary leading-snug">
                {s.value}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* ═══ Commons image with attribution ═══ */}
      {article.image && (
        <figure className="mb-8">
          {/* Plain img: external Commons host, attribution caption required by license */}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={article.image.url}
            alt={article.title}
            className="w-full rounded-2xl object-cover max-h-[420px]"
          />
          <figcaption className="text-[11px] text-outline mt-2">
            Photo:{" "}
            <a
              href={article.image.descriptionUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-primary underline"
            >
              {article.image.attribution}
            </a>{" "}
            via Wikimedia Commons &middot; {article.image.license}
          </figcaption>
        </figure>
      )}

      {/* ═══ Body — serif, editorial measure, drop cap on the opening graf ═══ */}
      <div className="space-y-6">
        {article.sections.map((section, i) => (
          <section key={i}>
            {section.heading && (
              <h2 className="font-headline text-xl font-bold text-on-surface mb-3">
                {section.heading}
              </h2>
            )}
            <div className="space-y-4">
              {section.paragraphs.map((p, j) => (
                <p
                  key={j}
                  className={`font-serif text-[17px] text-on-surface-variant leading-[1.65] ${
                    i === 0 && j === 0
                      ? "first-letter:font-headline first-letter:text-5xl first-letter:font-black first-letter:text-primary first-letter:float-left first-letter:mr-2 first-letter:leading-[0.85] first-letter:mt-1"
                      : ""
                  }`}
                >
                  {p}
                </p>
              ))}
            </div>
          </section>
        ))}
      </div>

      {/* ═══ Sources ═══ */}
      {article.sources.length > 0 && (
        <footer className="mt-10 pt-6 border-t border-outline-variant/20">
          <h2 className="text-[11px] uppercase tracking-[0.15em] text-outline mb-3">
            Sources
          </h2>
          <ul className="space-y-2">
            {article.sources.map((s) => (
              <li key={s.url}>
                <a
                  href={s.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[13px] text-secondary hover:text-primary transition-colors"
                >
                  {s.title}{" "}
                  <span className="text-outline">&middot; {s.source}</span>
                </a>
              </li>
            ))}
          </ul>
        </footer>
      )}

      {/* ═══ Methodology note ═══ */}
      <p className="mt-8 text-[11px] text-outline leading-relaxed">
        How this was made: drafted by the MatchPrism editorial model from verified
        fixture data and the cited reports above, then passed through an automated
        fact-grounding and style edit. Fixture data: fixturedownload.com. Corrections:
        flag anything wrong via the feedback link in the footer.
      </p>
    </article>
  );
}
