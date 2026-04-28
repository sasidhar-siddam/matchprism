/**
 * Data loader — reads pre-computed JSON from data/processed/.
 * Used by server components at build time (SSG).
 */
import fs from "fs";
import path from "path";

const DATA_DIR = path.join(process.cwd(), "data", "processed");

function readJSON<T>(filePath: string): T {
  const raw = fs.readFileSync(filePath, "utf-8");
  return JSON.parse(raw) as T;
}

// ── Schedule ──
export interface ScheduleEntry {
  slug: string;
  date: string;
  dateRaw: string;
  time: string;
  team1: string;
  team2: string;
  team1Full: string;
  team2Full: string;
  venue: string;
  city: string;
  team1WinProb: number;
  team2WinProb: number;
  modelConfidence: number;
}

export function getSchedule(): ScheduleEntry[] {
  return readJSON<ScheduleEntry[]>(path.join(DATA_DIR, "schedule.json"));
}

// ── Match Data ──
export interface MatchVenue {
  name: string;
  city: string;
  totalMatches: number;
  avg1stInnings: number;
  avg2ndInnings: number;
  chaseWinPct: number;
  tossBatFirstPct: number;
  tossBowlFirstPct: number;
  paceWicketPct: number;
  spinWicketPct: number;
  powerplayAvg: number;
  middleOversAvg: number;
  deathOversAvg: number;
  highestTotal: number;
  lowestTotal: number;
  venueRunRate: number;
  boundariesPerInnings: number;
  sixesPerInnings: number;
  foursPerInnings: number;
  verdict: string;
  altitude_m?: number;
  boundary_avg_m?: number;
  altitudeEffect?: { ball_travel_bonus_pct: number; impact: string };
  recentForm?: {
    last10: { avg1stInnings: number; avgRunRate: number; chaseWinPct: number; avgSixes: number };
    last20: { avg1stInnings: number; avgRunRate: number; chaseWinPct: number; avgSixes: number };
    trend: string;
  };
  scoringTimeline?: Array<{
    date: string;
    league: string;
    firstInningsTotal: number;
    secondInningsTotal: number;
    firstInningsRR: number;
    winner: string;
  }>;
}

export interface MatchCaptainPick {
  playerName: string;
  team: string;
  role: string;
  grade: string;
  venueAvg: number;
  venueSR: number;
  venueEcon?: number;
  last5: string[];
  reasoning: string;
  projectedPoints: string;
}

export interface MatchAvoidPick {
  playerName: string;
  team: string;
  grade: string;
  reason: string;
}

export interface MatchH2HEntry {
  date: string;
  venue: string;
  team1: string;
  team1Score: string;
  team2: string;
  team2Score: string;
  winner: string;
  margin: string;
}

export interface MatchPlayerFit {
  name: string;
  team: string;
  role: string;
  venueAvg: number;
  venueSR: number;
  venueEcon?: number;
  grade: string;
  last5: string[];
  overallAvg: number;
}

export interface MatchAnalysisRow {
  outcome: string;
  modelProb: number;
  impliedProb: number;
  edge: number;
  verdict: "VALUE" | "FAIR" | "AVOID";
}

export interface MatchData {
  slug: string;
  date: string;
  dateRaw: string;
  time: string;
  team1: string;
  team2: string;
  team1Full: string;
  team2Full: string;
  venue: MatchVenue;
  team1WinProb: number;
  team2WinProb: number;
  modelConfidence: number;
  captainPicks: MatchCaptainPick[];
  avoidPicks: MatchAvoidPick[];
  h2h: {
    team1Wins: number;
    team2Wins: number;
    recentMatches: MatchH2HEntry[];
  };
  playerFit: {
    team1: MatchPlayerFit[];
    team2: MatchPlayerFit[];
  };
  advancedAnalysis: MatchAnalysisRow[];
}

export function getMatch(slug: string): MatchData | null {
  const matchesDir = path.join(DATA_DIR, "matches");
  const files = fs.readdirSync(matchesDir);
  const matchFile = files.find((f) => f.includes(slug) && f.endsWith(".json"));
  if (!matchFile) return null;
  return readJSON<MatchData>(path.join(matchesDir, matchFile));
}

export function getAllMatchSlugs(): string[] {
  const matchesDir = path.join(DATA_DIR, "matches");
  if (!fs.existsSync(matchesDir)) return [];
  return fs
    .readdirSync(matchesDir)
    .filter((f) => f.endsWith(".json"))
    .map((f) => {
      const match = readJSON<MatchData>(path.join(matchesDir, f));
      return match.slug;
    });
}

// ── Pitch Reports ──
export interface PitchReport {
  venue: string;
  matchDate: string;
  matchTime: string;
  weatherSource: string;
  weather: {
    temperature: number;
    humidity: number;
    windSpeed: number;
    windUnit: string;
    cloudCover: number;
    dewPoint: number | null;
    description: string;
  };
  dewAnalysis: {
    probability: number;
    impact: string;
    secondInningsAdvantage: boolean;
  };
  pitchBehavior: {
    swingPotential: number;
    spinPotential: number;
    paceFriendly: boolean;
    spinFriendly: boolean;
  };
  phaseAnalysis: {
    month: number;
    sampleSize: number;
    powerplay: { firstInnings: number; secondInnings: number; delta: number };
    middleOvers: { firstInnings: number; secondInnings: number; delta: number };
    deathOvers: { firstInnings: number; secondInnings: number; delta: number };
    totalFirst: number;
    totalSecond: number;
    scoringDelta: number;
  };
  tossIntelligence: {
    recommendation: string;
    bowlFirstProbability: number;
    confidence: number;
    reasoning: string[];
  };
  verdict: string;
  reasoning: string[];
}

export function getPitchReport(slug: string): PitchReport | null {
  const pitchPath = path.join(DATA_DIR, "pitch_reports.json");
  if (!fs.existsSync(pitchPath)) return null;
  const reports = readJSON<Record<string, PitchReport>>(pitchPath);
  return reports[slug] || null;
}

// ── Odds ──
export interface TeamOddsEntry {
  team: string;
  decimalOdds: number;
  record: {
    played: number;
    won: number;
    lost: number;
    noResult?: number;
    points: number;
    nrr: number;
  };
  modelTitleProb: number;
  reasoning: string;
}

export interface OddsData {
  lastUpdated: string;
  source: string;
  overround: number;
  tournamentWinner: TeamOddsEntry[];
  matchOdds: Record<string, { team1Odds: number; team2Odds: number }>;
}

export function getOdds(): OddsData {
  const oddsPath = path.join(DATA_DIR, "odds.json");
  if (!fs.existsSync(oddsPath)) {
    return { lastUpdated: "", source: "", overround: 0, tournamentWinner: [], matchOdds: {} };
  }
  return readJSON<OddsData>(oddsPath);
}

// ── Venues ──

/** Convert a venue name to a URL-friendly slug: "M Chinnaswamy Stadium" -> "m-chinnaswamy-stadium" */
export function venueToSlug(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}

/**
 * Look up a venue by slug. Supports both exact slug match
 * (e.g. "m-chinnaswamy-stadium") and partial match (e.g. "chinnaswamy").
 */
export function getVenue(slug: string): (MatchVenue & { paceWicketPct?: number; spinWicketPct?: number }) | null {
  const venuesPath = path.join(DATA_DIR, "venues.json");
  if (!fs.existsSync(venuesPath)) return null;
  const venues = readJSON<Record<string, Record<string, unknown>>>(venuesPath);

  // Try exact slug match first
  for (const [name, data] of Object.entries(venues)) {
    if (venueToSlug(name) === slug) {
      return data as unknown as MatchVenue;
    }
  }

  // Partial match: slug "chinnaswamy" should match "M Chinnaswamy Stadium"
  for (const [name, data] of Object.entries(venues)) {
    if (venueToSlug(name).includes(slug)) {
      return data as unknown as MatchVenue;
    }
  }

  return null;
}

/** Return slugs for all venues with 20+ matches (skip obscure ones). */
export function getAllVenueSlugs(): string[] {
  const venuesPath = path.join(DATA_DIR, "venues.json");
  if (!fs.existsSync(venuesPath)) return [];
  const venues = readJSON<Record<string, { totalMatches?: number }>>(venuesPath);
  return Object.entries(venues)
    .filter(([, v]) => (v.totalMatches ?? 0) >= 20)
    .map(([name]) => venueToSlug(name));
}

/** Return schedule entries whose venue matches a given venue name (case-insensitive). */
export function getScheduleForVenue(venueName: string): ScheduleEntry[] {
  const schedule = getSchedule();
  const lower = venueName.toLowerCase();
  return schedule.filter((s) => s.venue.toLowerCase() === lower);
}

// ── Players ──

/** Convert a player name to a URL-friendly slug: "V Kohli" -> "v-kohli", "JJ Bumrah" -> "jj-bumrah" */
export function nameToSlug(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function getPlayer(slug: string): any | null {
  const playersPath = path.join(DATA_DIR, "players.json");
  if (!fs.existsSync(playersPath)) return null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const players = readJSON<Record<string, any>>(playersPath);

  for (const [name, data] of Object.entries(players)) {
    if (nameToSlug(name) === slug) {
      return { ...data, name };
    }
  }
  return null;
}

/**
 * Return slugs for all players who appear in IPL 2026 match squads.
 * Reads schedule.json for match slugs, then each match JSON for playerFit names.
 */
export function getAllPlayerSlugs(): string[] {
  const matchesDir = path.join(DATA_DIR, "matches");
  if (!fs.existsSync(matchesDir)) return [];

  const files = fs.readdirSync(matchesDir).filter((f) => f.endsWith(".json"));
  const nameSet = new Set<string>();

  for (const file of files) {
    const match = readJSON<MatchData>(path.join(matchesDir, file));
    if (match.playerFit) {
      for (const p of [...(match.playerFit.team1 || []), ...(match.playerFit.team2 || [])]) {
        nameSet.add(p.name);
      }
    }
  }

  return [...nameSet].map((n) => nameToSlug(n));
}

/**
 * Build a lookup of player name -> IPL team code from match data.
 * Returns the most recent team code found for each player.
 */
export function getPlayerTeamMap(): Record<string, string> {
  const matchesDir = path.join(DATA_DIR, "matches");
  if (!fs.existsSync(matchesDir)) return {};

  const files = fs.readdirSync(matchesDir).filter((f) => f.endsWith(".json"));
  const map: Record<string, string> = {};

  for (const file of files) {
    const match = readJSON<MatchData>(path.join(matchesDir, file));
    if (match.playerFit) {
      for (const p of [...(match.playerFit.team1 || []), ...(match.playerFit.team2 || [])]) {
        map[p.name] = p.team;
      }
    }
  }

  return map;
}
