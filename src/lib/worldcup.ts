/**
 * World Cup 2026 data loader — reads pre-computed JSON from
 * data/processed/worldcup/. All loaders degrade gracefully when a file
 * is missing so the cricket build never breaks if the WC pipeline
 * hasn't run.
 */
import fs from "fs";
import path from "path";

const WC_DIR = path.join(process.cwd(), "data", "processed", "worldcup");

function readJSON<T>(file: string): T | null {
  const p = path.join(WC_DIR, file);
  if (!fs.existsSync(p)) return null;
  return JSON.parse(fs.readFileSync(p, "utf-8")) as T;
}

// ── Schedule ──
export interface WCMatch {
  matchNumber: number;
  slug: string;
  stage: string;
  matchday: number | null;
  group: string | null;
  dateRaw: string;
  date: string;
  time: string;
  homeTeam: string;
  awayTeam: string;
  venue: string;
  city: string;
  homeScore: number | null;
  awayScore: number | null;
  winner: string | null;
  status: "played" | "upcoming";
}

export interface WCSchedule {
  fetchedAt: string;
  source: string;
  totalMatches: number;
  playedMatches: number;
  groups: string[];
  matches: WCMatch[];
}

export function getWCSchedule(): WCSchedule | null {
  return readJSON<WCSchedule>("schedule.json");
}

// ── News ──
export interface WCNewsItem {
  title: string;
  url: string;
  source: string;
  published: string | null;
  summary: string;
}

export function getWCNews(): { fetchedAt: string; items: WCNewsItem[] } | null {
  return readJSON<{ fetchedAt: string; items: WCNewsItem[] }>("news.json");
}

// ── Digest (claude -p output) ──
export interface WCMatchPreview {
  matchNumber: number;
  slug: string;
  headline: string;
  preview: string;
  keyFact: string;
}

export interface WCDigest {
  dailyBrief: string;
  matchPreviews: WCMatchPreview[];
  topStories: WCNewsItem[];
  generator: string;
  generatedAt: string;
}

export function getWCDigest(): WCDigest | null {
  return readJSON<WCDigest>("digest.json");
}

// ── Articles (claude -p output, styled by the worldcup-article skill) ──
export interface WCArticleSection {
  heading: string | null;
  paragraphs: string[];
}

export interface WCArticleImage {
  url: string;
  attribution: string;
  license: string;
  descriptionUrl: string;
}

export interface WCArticle {
  slug: string;
  title: string;
  dek: string;
  category: "Match Preview" | "Match Recap" | "Analysis";
  keyStats: { label: string; value: string }[];
  sections: WCArticleSection[];
  sources: { title: string; url: string; source: string }[];
  image: WCArticleImage | null;
  publishedAt: string;
  generator: string;
}

export function getWCArticles(): WCArticle[] {
  const data = readJSON<{ articles: WCArticle[] }>("articles.json");
  return data?.articles ?? [];
}

export function getWCArticle(slug: string): WCArticle | null {
  return getWCArticles().find((a) => a.slug === slug) ?? null;
}

/** Approximate reading time in minutes from article body length. */
export function readingTime(article: WCArticle): number {
  const words = article.sections
    .flatMap((s) => s.paragraphs)
    .join(" ")
    .split(/\s+/).length;
  return Math.max(1, Math.round(words / 220));
}

// ── Derived helpers ──

/** Next matches that haven't been played yet, in match-number order. */
export function getUpcomingWCMatches(schedule: WCSchedule, limit = 9): WCMatch[] {
  return schedule.matches.filter((m) => m.status === "upcoming").slice(0, limit);
}

export interface WCGroupRow {
  team: string;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goalsFor: number;
  goalsAgainst: number;
  goalDiff: number;
  points: number;
}

/** Compute live group tables from played group-stage matches. */
export function getWCGroupTables(schedule: WCSchedule): Record<string, WCGroupRow[]> {
  const tables: Record<string, Record<string, WCGroupRow>> = {};

  const row = (group: string, team: string): WCGroupRow => {
    tables[group] ??= {};
    tables[group][team] ??= {
      team, played: 0, won: 0, drawn: 0, lost: 0,
      goalsFor: 0, goalsAgainst: 0, goalDiff: 0, points: 0,
    };
    return tables[group][team];
  };

  for (const m of schedule.matches) {
    if (!m.group) continue;
    const home = row(m.group, m.homeTeam);
    const away = row(m.group, m.awayTeam);
    if (m.status !== "played" || m.homeScore === null || m.awayScore === null) continue;

    home.played++; away.played++;
    home.goalsFor += m.homeScore; home.goalsAgainst += m.awayScore;
    away.goalsFor += m.awayScore; away.goalsAgainst += m.homeScore;
    if (m.homeScore > m.awayScore) { home.won++; home.points += 3; away.lost++; }
    else if (m.homeScore < m.awayScore) { away.won++; away.points += 3; home.lost++; }
    else { home.drawn++; away.drawn++; home.points++; away.points++; }
  }

  const result: Record<string, WCGroupRow[]> = {};
  for (const group of Object.keys(tables).sort()) {
    const rows = Object.values(tables[group]);
    for (const r of rows) r.goalDiff = r.goalsFor - r.goalsAgainst;
    rows.sort(
      (a, b) =>
        b.points - a.points ||
        b.goalDiff - a.goalDiff ||
        b.goalsFor - a.goalsFor ||
        a.team.localeCompare(b.team),
    );
    result[group] = rows;
  }
  return result;
}
