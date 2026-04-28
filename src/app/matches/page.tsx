import Link from "next/link";
import { getSchedule } from "@/lib/data";
import { getTeam, getTeamColorClass } from "@/lib/teams";
import type { TeamCode } from "@/lib/types";

export const metadata = {
  title: "IPL 2026 Schedule | MatchPrism",
  description: "Full IPL 2026 match schedule with win probabilities, venue intelligence, and captain picks for every fixture.",
};

export default function MatchesPage() {
  const schedule = getSchedule();

  return (
    <div className="py-8 space-y-8">
      <div>
        <h1 className="font-headline text-3xl md:text-4xl font-black text-on-surface">
          IPL 2026 Schedule
        </h1>
        <p className="text-secondary mt-2">
          {schedule.length} matches with full intelligence reports
        </p>
      </div>

      <div className="space-y-3">
        {schedule.map((match) => {
          const t1 = getTeam(match.team1);
          const t2 = getTeam(match.team2);
          const t1Color = getTeamColorClass(match.team1 as TeamCode);
          const t2Color = getTeamColorClass(match.team2 as TeamCode);

          return (
            <Link
              key={match.slug}
              href={`/match/${match.slug}`}
              className="flex items-center justify-between p-5 bg-surface-container rounded-2xl hover:bg-surface-container-high transition-colors group"
            >
              <div className="flex items-center gap-5">
                <div className="flex -space-x-2">
                  <div className={`w-10 h-10 rounded-full ${t1Color} flex items-center justify-center text-[11px] font-bold text-white border-2 border-surface-container`}>
                    {match.team1}
                  </div>
                  <div className={`w-10 h-10 rounded-full ${t2Color} flex items-center justify-center text-[11px] font-bold text-white border-2 border-surface-container`}>
                    {match.team2}
                  </div>
                </div>
                <div>
                  <h3 className="font-headline font-bold text-on-surface">
                    {t1.name} vs {t2.name}
                  </h3>
                  <p className="text-[13px] text-secondary mt-0.5">
                    {match.venue}, {match.city}
                  </p>
                </div>
              </div>

              <div className="text-right hidden sm:block">
                <p className="text-sm font-medium text-on-surface">{match.date}</p>
                <p className="text-[12px] text-primary font-bold">{match.time}</p>
                <p className="text-[12px] text-secondary mt-1">
                  {match.team1} {match.team1WinProb}% — {match.team2} {match.team2WinProb}%
                </p>
              </div>

              <span className="text-on-surface/30 group-hover:text-primary transition-colors ml-3">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                </svg>
              </span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
