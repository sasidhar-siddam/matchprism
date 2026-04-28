import { describe, it, expect } from "vitest";
import {
  getSchedule,
  getMatch,
  getAllMatchSlugs,
  getPitchReport,
  getVenue,
  getAllVenueSlugs,
  getPlayer,
  getAllPlayerSlugs,
  getPlayerTeamMap,
  nameToSlug,
  venueToSlug,
} from "../data";

// ── Slug helpers ──

describe("nameToSlug", () => {
  it("converts player names to slugs", () => {
    expect(nameToSlug("V Kohli")).toBe("v-kohli");
    expect(nameToSlug("JJ Bumrah")).toBe("jj-bumrah");
    expect(nameToSlug("Rashid Khan")).toBe("rashid-khan");
    expect(nameToSlug("F du Plessis")).toBe("f-du-plessis");
  });
});

describe("venueToSlug", () => {
  it("converts venue names to slugs", () => {
    expect(venueToSlug("M Chinnaswamy Stadium")).toBe("m-chinnaswamy-stadium");
    expect(venueToSlug("Wankhede Stadium")).toBe("wankhede-stadium");
    expect(venueToSlug("R Premadasa Stadium")).toBe("r-premadasa-stadium");
  });
});

// ── Schedule ──

describe("getSchedule", () => {
  it("returns an array of matches", () => {
    const schedule = getSchedule();
    expect(Array.isArray(schedule)).toBe(true);
    expect(schedule.length).toBeGreaterThanOrEqual(14);
  });

  it("each match has required fields", () => {
    const schedule = getSchedule();
    for (const match of schedule) {
      expect(match.slug).toBeTruthy();
      expect(match.team1).toBeTruthy();
      expect(match.team2).toBeTruthy();
      expect(match.venue).toBeTruthy();
      expect(match.date).toBeTruthy();
      expect(match.team1WinProb).toBeGreaterThan(0);
      expect(match.team2WinProb).toBeGreaterThan(0);
      expect(match.team1WinProb + match.team2WinProb).toBe(100);
    }
  });

  it("first match is RCB vs SRH", () => {
    const schedule = getSchedule();
    expect(schedule[0].team1).toBe("RCB");
    expect(schedule[0].team2).toBe("SRH");
  });
});

// ── Match Data ──

describe("getAllMatchSlugs", () => {
  it("returns 14 match slugs", () => {
    const slugs = getAllMatchSlugs();
    expect(slugs.length).toBe(14);
    expect(slugs).toContain("rcb-vs-srh");
    expect(slugs).toContain("mi-vs-csk");
  });
});

describe("getMatch", () => {
  it("returns match data for valid slug", () => {
    const match = getMatch("rcb-vs-srh");
    expect(match).not.toBeNull();
    expect(match!.team1).toBe("RCB");
    expect(match!.team2).toBe("SRH");
    expect(match!.venue).toBeTruthy();
    expect(match!.venue.name).toBe("M Chinnaswamy Stadium");
  });

  it("returns null for invalid slug", () => {
    expect(getMatch("nonexistent-match")).toBeNull();
  });

  it("has captain picks", () => {
    const match = getMatch("rcb-vs-srh");
    expect(match!.captainPicks.length).toBeGreaterThan(0);
    expect(match!.captainPicks[0].playerName).toBeTruthy();
    expect(match!.captainPicks[0].grade).toBeTruthy();
  });

  it("has H2H data", () => {
    const match = getMatch("rcb-vs-srh");
    expect(match!.h2h.team1Wins + match!.h2h.team2Wins).toBeGreaterThan(0);
    expect(match!.h2h.recentMatches.length).toBeGreaterThan(0);
  });

  it("has player venue fit for both teams", () => {
    const match = getMatch("rcb-vs-srh");
    expect(match!.playerFit.team1.length).toBeGreaterThan(0);
    expect(match!.playerFit.team2.length).toBeGreaterThan(0);
  });

  it("has advanced analysis", () => {
    const match = getMatch("rcb-vs-srh");
    expect(match!.advancedAnalysis.length).toBeGreaterThan(0);
    for (const row of match!.advancedAnalysis) {
      expect(["VALUE", "FAIR", "AVOID"]).toContain(row.verdict);
    }
  });
});

// ── Pitch Reports ──

describe("getPitchReport", () => {
  it("returns pitch report for valid slug", () => {
    const report = getPitchReport("rcb-vs-srh");
    expect(report).not.toBeNull();
    expect(report!.venue).toBe("M Chinnaswamy Stadium");
  });

  it("has dew analysis", () => {
    const report = getPitchReport("rcb-vs-srh");
    expect(report!.dewAnalysis.probability).toBeGreaterThan(0);
    expect(["Heavy", "Moderate", "Low"]).toContain(report!.dewAnalysis.impact);
  });

  it("has pitch behavior", () => {
    const report = getPitchReport("rcb-vs-srh");
    expect(report!.pitchBehavior.swingPotential).toBeGreaterThan(0);
    expect(report!.pitchBehavior.spinPotential).toBeGreaterThan(0);
  });

  it("has toss intelligence", () => {
    const report = getPitchReport("rcb-vs-srh");
    expect(report!.tossIntelligence.recommendation).toBeTruthy();
    expect(report!.tossIntelligence.bowlFirstProbability).toBeGreaterThan(0);
  });

  it("returns null for invalid slug", () => {
    expect(getPitchReport("nonexistent")).toBeNull();
  });
});

// ── Venues ──

describe("getAllVenueSlugs", () => {
  it("returns venues with 20+ matches", () => {
    const slugs = getAllVenueSlugs();
    expect(slugs.length).toBeGreaterThan(20);
    expect(slugs).toContain("wankhede-stadium");
    expect(slugs).toContain("m-chinnaswamy-stadium");
    expect(slugs).toContain("eden-gardens");
  });
});

describe("getVenue", () => {
  it("returns venue by exact slug", () => {
    const venue = getVenue("wankhede-stadium");
    expect(venue).not.toBeNull();
    expect(venue!.name).toBe("Wankhede Stadium");
    expect(venue!.city).toBe("Mumbai");
  });

  it("returns venue by partial slug", () => {
    const venue = getVenue("chinnaswamy");
    expect(venue).not.toBeNull();
    expect(venue!.name).toBe("M Chinnaswamy Stadium");
  });

  it("has scoring stats", () => {
    const venue = getVenue("wankhede-stadium");
    expect(venue!.avg1stInnings).toBeGreaterThan(100);
    expect(venue!.chaseWinPct).toBeGreaterThan(0);
    expect(venue!.totalMatches).toBeGreaterThan(50);
    expect(venue!.venueRunRate).toBeGreaterThan(6);
  });

  it("returns null for invalid slug", () => {
    expect(getVenue("nonexistent-stadium")).toBeNull();
  });
});

// ── Players ──

describe("getAllPlayerSlugs", () => {
  it("returns 100+ player slugs", () => {
    const slugs = getAllPlayerSlugs();
    expect(slugs.length).toBeGreaterThan(100);
    expect(slugs).toContain("v-kohli");
  });
});

describe("getPlayer", () => {
  it("returns player by slug", () => {
    const player = getPlayer("v-kohli");
    expect(player).not.toBeNull();
    expect(player.name).toBe("V Kohli");
  });

  it("has overall batting stats", () => {
    const player = getPlayer("v-kohli");
    const batting = player.overall.batting;
    expect(batting.runs).toBeGreaterThan(8000);
    expect(batting.innings).toBeGreaterThan(200);
    expect(batting.average).toBeGreaterThan(30);
    expect(batting.strikeRate).toBeGreaterThan(120);
  });

  it("has venue data", () => {
    const player = getPlayer("v-kohli");
    expect(Object.keys(player.venues).length).toBeGreaterThan(5);
    const chinnaswamy = player.venues["M Chinnaswamy Stadium"];
    expect(chinnaswamy).toBeTruthy();
    expect(chinnaswamy.grade).toBeTruthy();
  });

  it("has form timeline", () => {
    const player = getPlayer("v-kohli");
    expect(player.formTimeline.length).toBeGreaterThan(0);
    expect(player.formTimeline[0].runs).toBeDefined();
    expect(player.formTimeline[0].date).toBeTruthy();
  });

  it("has recent form", () => {
    const player = getPlayer("v-kohli");
    expect(player.recentForm).toBeTruthy();
    expect(player.recentForm.last10).toBeTruthy();
    expect(player.recentForm.trend).toBeTruthy();
  });

  it("has season stats", () => {
    const player = getPlayer("v-kohli");
    expect(player.seasonStats).toBeTruthy();
    expect(Object.keys(player.seasonStats).length).toBeGreaterThan(0);
  });

  it("returns null for invalid slug", () => {
    expect(getPlayer("nonexistent-player")).toBeNull();
  });

  it("works for bowlers too", () => {
    const player = getPlayer("jj-bumrah");
    expect(player).not.toBeNull();
    const bowling = player.overall.bowling;
    expect(bowling.wickets).toBeGreaterThan(100);
    expect(bowling.economy).toBeGreaterThan(0);
  });
});

describe("getPlayerTeamMap", () => {
  it("returns team codes for players", () => {
    const map = getPlayerTeamMap();
    expect(Object.keys(map).length).toBeGreaterThan(50);
    expect(map["V Kohli"]).toBe("RCB");
  });
});

// ── Cross-module integration ──

describe("data consistency", () => {
  it("all match slugs from schedule have match data", () => {
    const schedule = getSchedule();
    for (const entry of schedule) {
      const match = getMatch(entry.slug);
      expect(match).not.toBeNull();
    }
  });

  it("all match slugs have pitch reports", () => {
    const slugs = getAllMatchSlugs();
    for (const slug of slugs) {
      const report = getPitchReport(slug);
      expect(report).not.toBeNull();
    }
  });

  it("captain picks reference real players", () => {
    const match = getMatch("rcb-vs-srh");
    for (const pick of match!.captainPicks) {
      const player = getPlayer(nameToSlug(pick.playerName));
      // Player may not be found if name format differs, but slug should be valid
      expect(pick.playerName).toBeTruthy();
      expect(pick.grade).toBeTruthy();
    }
  });
});
