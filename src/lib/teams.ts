import type { TeamCode } from "./types";

export interface TeamMeta {
  code: TeamCode;
  name: string;
  shortName: string;
  color: string;
  homeVenue: string;
  homeCity: string;
}

export const teams: Record<TeamCode, TeamMeta> = {
  RCB: {
    code: "RCB",
    name: "Royal Challengers Bengaluru",
    shortName: "Challengers",
    color: "var(--color-team-rcb)",
    homeVenue: "M. Chinnaswamy Stadium",
    homeCity: "Bengaluru",
  },
  SRH: {
    code: "SRH",
    name: "Sunrisers Hyderabad",
    shortName: "Sunrisers",
    color: "var(--color-team-srh)",
    homeVenue: "Rajiv Gandhi International Stadium",
    homeCity: "Hyderabad",
  },
  CSK: {
    code: "CSK",
    name: "Chennai Super Kings",
    shortName: "Super Kings",
    color: "var(--color-team-csk)",
    homeVenue: "MA Chidambaram Stadium",
    homeCity: "Chennai",
  },
  MI: {
    code: "MI",
    name: "Mumbai Indians",
    shortName: "Indians",
    color: "var(--color-team-mi)",
    homeVenue: "Wankhede Stadium",
    homeCity: "Mumbai",
  },
  KKR: {
    code: "KKR",
    name: "Kolkata Knight Riders",
    shortName: "Knight Riders",
    color: "var(--color-team-kkr)",
    homeVenue: "Eden Gardens",
    homeCity: "Kolkata",
  },
  DC: {
    code: "DC",
    name: "Delhi Capitals",
    shortName: "Capitals",
    color: "var(--color-team-dc)",
    homeVenue: "Arun Jaitley Stadium",
    homeCity: "Delhi",
  },
  RR: {
    code: "RR",
    name: "Rajasthan Royals",
    shortName: "Royals",
    color: "var(--color-team-rr)",
    homeVenue: "Sawai Mansingh Stadium",
    homeCity: "Jaipur",
  },
  PBKS: {
    code: "PBKS",
    name: "Punjab Kings",
    shortName: "Kings",
    color: "var(--color-team-pbks)",
    homeVenue: "IS Bindra Stadium",
    homeCity: "Mohali",
  },
  GT: {
    code: "GT",
    name: "Gujarat Titans",
    shortName: "Titans",
    color: "var(--color-team-gt)",
    homeVenue: "Narendra Modi Stadium",
    homeCity: "Ahmedabad",
  },
  LSG: {
    code: "LSG",
    name: "Lucknow Super Giants",
    shortName: "Super Giants",
    color: "var(--color-team-lsg)",
    homeVenue: "BRSABV Ekana Cricket Stadium",
    homeCity: "Lucknow",
  },
};

export function getTeam(code: string): TeamMeta {
  return teams[code as TeamCode] ?? teams.RCB;
}

export function getTeamColorClass(code: TeamCode): string {
  const map: Record<TeamCode, string> = {
    RCB: "bg-team-rcb",
    SRH: "bg-team-srh",
    CSK: "bg-team-csk",
    MI: "bg-team-mi",
    KKR: "bg-team-kkr",
    DC: "bg-team-dc",
    RR: "bg-team-rr",
    PBKS: "bg-team-pbks",
    GT: "bg-team-gt",
    LSG: "bg-team-lsg",
  };
  return map[code];
}
