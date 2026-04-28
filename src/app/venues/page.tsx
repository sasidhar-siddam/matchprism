import Link from "next/link";
import fs from "fs";
import path from "path";
import { venueToSlug } from "@/lib/data";

export const metadata = {
  title: "T20 Venues | MatchPrism",
  description: "Analytics for 350+ cricket venues worldwide. Scoring trends, phase dynamics, toss intelligence, and conditions analysis.",
};

interface VenueEntry {
  name: string;
  city: string;
  totalMatches: number;
  avg1stInnings: number;
  chaseWinPct: number;
  venueRunRate: number;
  sixesPerInnings: number;
  leagues: string[];
  verdict: string;
  recentForm?: {
    trend: string;
  };
}

function loadVenues(): VenueEntry[] {
  const venuesPath = path.join(process.cwd(), "data", "processed", "venues.json");
  const raw = JSON.parse(fs.readFileSync(venuesPath, "utf-8"));
  return Object.entries(raw)
    .map(([name, data]) => ({ name, ...(data as Omit<VenueEntry, "name">) }))
    .filter((v) => v.totalMatches >= 10)
    .sort((a, b) => b.totalMatches - a.totalMatches);
}

export default function VenuesPage() {
  const venues = loadVenues();

  return (
    <div className="py-8 space-y-8">
      <div>
        <h1 className="font-headline text-3xl md:text-4xl font-black text-on-surface">
          Venue Intelligence
        </h1>
        <p className="text-secondary mt-2">
          {venues.length} venues with 10+ T20 matches analysed
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {venues.map((venue) => {
          const slug = venueToSlug(venue.name);
          const trend = venue.recentForm?.trend;

          return (
            <Link
              key={venue.name}
              href={`/venue/${slug}`}
              className="bg-surface-container rounded-2xl p-5 hover:bg-surface-container-high transition-colors group"
            >
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h3 className="font-headline font-bold text-on-surface group-hover:text-primary transition-colors">
                    {venue.name}
                  </h3>
                  <p className="text-[13px] text-secondary">{venue.city}</p>
                </div>
                <span className="text-[11px] font-bold text-outline bg-surface-container-highest px-2 py-1 rounded-lg">
                  {venue.totalMatches} matches
                </span>
              </div>

              <div className="grid grid-cols-3 gap-3 mt-4">
                <div>
                  <p className="text-[11px] text-outline uppercase tracking-wider">Avg Score</p>
                  <p className="font-headline font-bold text-primary text-lg">{Math.round(venue.avg1stInnings)}</p>
                </div>
                <div>
                  <p className="text-[11px] text-outline uppercase tracking-wider">Chase %</p>
                  <p className="font-headline font-bold text-on-surface text-lg">{venue.chaseWinPct}%</p>
                </div>
                <div>
                  <p className="text-[11px] text-outline uppercase tracking-wider">Run Rate</p>
                  <p className="font-headline font-bold text-on-surface text-lg">{venue.venueRunRate}</p>
                </div>
              </div>

              <div className="flex items-center gap-2 mt-4 pt-3 border-t border-outline-variant/10">
                <div className="flex gap-1">
                  {venue.leagues?.slice(0, 4).map((l) => (
                    <span key={l} className="text-[11px] bg-surface-container-highest px-1.5 py-0.5 rounded text-secondary uppercase">
                      {l}
                    </span>
                  ))}
                  {(venue.leagues?.length ?? 0) > 4 && (
                    <span className="text-[11px] text-outline">+{venue.leagues.length - 4}</span>
                  )}
                </div>
                {trend && (
                  <span className={`text-[11px] font-medium ml-auto ${
                    trend === "scoring_up" ? "text-grade-aplus" : trend === "scoring_down" ? "text-grade-d" : "text-secondary"
                  }`}>
                    {trend === "scoring_up" ? "Scoring Up" : trend === "scoring_down" ? "Scoring Down" : "Stable"}
                  </span>
                )}
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
