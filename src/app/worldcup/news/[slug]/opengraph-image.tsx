import { ImageResponse } from "next/og";
import { getWCArticle, getWCArticles } from "@/lib/worldcup";

export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export function generateStaticParams() {
  return getWCArticles().map((a) => ({ slug: a.slug }));
}

export default async function OGImage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const article = getWCArticle(slug);
  const title = article?.title ?? "World Cup 2026 Intelligence";
  const category = article?.category ?? "Analysis";
  const stats = (article?.keyStats ?? []).slice(0, 3);

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: 64,
          background: "linear-gradient(135deg, #101418 0%, #1b2127 55%, #101418 100%)",
          color: "#e2e8f0",
          fontFamily: "sans-serif",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ display: "flex", alignItems: "baseline", gap: 14 }}>
            <span style={{ fontSize: 38, fontWeight: 900, color: "#7dd3fc", letterSpacing: -1 }}>
              MatchPrism
            </span>
            <span style={{ fontSize: 18, color: "#64748b", textTransform: "uppercase", letterSpacing: 4 }}>
              World Cup 2026
            </span>
          </div>
          <span
            style={{
              fontSize: 18,
              color: "#7dd3fc",
              border: "2px solid #7dd3fc55",
              borderRadius: 999,
              padding: "8px 22px",
              textTransform: "uppercase",
              letterSpacing: 3,
            }}
          >
            {category}
          </span>
        </div>

        <div style={{ display: "flex", fontSize: 58, fontWeight: 800, lineHeight: 1.15, maxWidth: 1020 }}>
          {title}
        </div>

        <div style={{ display: "flex", gap: 16 }}>
          {stats.map((s) => (
            <div
              key={s.label}
              style={{
                display: "flex",
                flexDirection: "column",
                background: "#ffffff10",
                borderRadius: 20,
                padding: "18px 26px",
                maxWidth: 340,
              }}
            >
              <span style={{ fontSize: 15, color: "#94a3b8", textTransform: "uppercase", letterSpacing: 2 }}>
                {s.label}
              </span>
              <span style={{ fontSize: 26, fontWeight: 700, color: "#7dd3fc", marginTop: 6 }}>
                {s.value}
              </span>
            </div>
          ))}
        </div>
      </div>
    ),
    size,
  );
}
