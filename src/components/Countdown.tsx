"use client";

import { useState, useEffect } from "react";

interface CountdownProps {
  targetDate: string; // ISO date like "2026-03-28"
  targetTime: string; // like "19:30 IST"
}

// Timezone offsets from UTC in minutes
const TZ_OFFSETS: Record<string, number> = {
  IST: 330,    // India Standard Time: UTC+5:30
  AEDT: 660,   // Australian Eastern Daylight: UTC+11
  AEST: 600,   // Australian Eastern Standard: UTC+10
  GST: 240,    // Gulf Standard Time: UTC+4
  BST: 60,     // British Summer Time: UTC+1
  GMT: 0,
  UTC: 0,
  SAST: 120,   // South Africa Standard: UTC+2
  PKT: 300,    // Pakistan Standard: UTC+5
  SLT: 330,    // Sri Lanka Time: UTC+5:30
  AST: -240,   // Atlantic Standard (Caribbean): UTC-4
};

function parseMatchTime(date: string, time: string): Date {
  // Parse "19:30 IST" → UTC timestamp
  // All math done in UTC to avoid browser timezone issues
  const parts = time.trim().split(/\s+/);
  const timePart = parts[0]; // "19:30"
  const tzCode = parts[1] || "IST"; // default IST for IPL
  const [hours, minutes] = timePart.split(":").map(Number);

  const offsetMinutes = TZ_OFFSETS[tzCode] ?? 330; // fallback IST

  // Build UTC: start with the date at midnight UTC, add local hours,
  // then subtract the timezone offset to get UTC
  const utcMs =
    Date.UTC(
      Number(date.split("-")[0]),
      Number(date.split("-")[1]) - 1,
      Number(date.split("-")[2]),
      hours,
      minutes,
      0
    ) - offsetMinutes * 60 * 1000;

  return new Date(utcMs);
}

export function Countdown({ targetDate, targetTime }: CountdownProps) {
  const [timeLeft, setTimeLeft] = useState({ hours: 0, minutes: 0, seconds: 0, live: false, passed: false });

  useEffect(() => {
    const target = parseMatchTime(targetDate, targetTime);

    function update() {
      const now = new Date();
      const diff = target.getTime() - now.getTime();

      if (diff <= 0) {
        // Match has started or is about to
        if (diff > -3 * 60 * 60 * 1000) {
          // Within 3 hours of start = "LIVE"
          setTimeLeft({ hours: 0, minutes: 0, seconds: 0, live: true, passed: false });
        } else {
          setTimeLeft({ hours: 0, minutes: 0, seconds: 0, live: false, passed: true });
        }
        return;
      }

      const hours = Math.floor(diff / (1000 * 60 * 60));
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((diff % (1000 * 60)) / 1000);
      setTimeLeft({ hours, minutes, seconds, live: false, passed: false });
    }

    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, [targetDate, targetTime]);

  const pad = (n: number) => String(n).padStart(2, "0");

  if (timeLeft.live) {
    return (
      <div className="flex items-center gap-3 bg-surface-container-high/60 backdrop-blur-xl px-6 py-4 rounded-2xl border border-primary/20">
        <span className="relative flex h-3 w-3">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-grade-aplus opacity-75" />
          <span className="relative inline-flex rounded-full h-3 w-3 bg-grade-aplus" />
        </span>
        <span className="font-headline text-2xl font-bold text-grade-aplus tracking-wider">MATCH LIVE</span>
      </div>
    );
  }

  if (timeLeft.passed) {
    return (
      <div className="bg-surface-container-high/60 backdrop-blur-xl px-6 py-4 rounded-2xl">
        <span className="font-headline text-lg font-bold text-secondary tracking-wider">MATCH COMPLETED</span>
      </div>
    );
  }

  const segments = [
    { value: pad(timeLeft.hours), label: "Hours" },
    { value: pad(timeLeft.minutes), label: "Min" },
    { value: pad(timeLeft.seconds), label: "Sec" },
  ];

  return (
    <div className="flex items-center gap-1 bg-surface-container-high/60 backdrop-blur-xl px-5 py-3 rounded-2xl border border-outline-variant/10">
      <span className="text-[11px] uppercase tracking-[0.15em] text-outline mr-3 hidden sm:inline">
        Match starts in
      </span>
      {segments.map((seg, i) => (
        <div key={seg.label} className="flex items-center gap-1">
          <div className="bg-surface-container-lowest px-3 py-2 rounded-lg min-w-[44px] text-center">
            <span className="font-headline text-2xl font-bold text-primary block leading-none">
              {seg.value}
            </span>
            <span className="text-[11px] tracking-[0.15em] text-outline">{seg.label}</span>
          </div>
          {i < segments.length - 1 && (
            <span className="text-primary/40 font-headline text-xl mx-0.5">:</span>
          )}
        </div>
      ))}
    </div>
  );
}
