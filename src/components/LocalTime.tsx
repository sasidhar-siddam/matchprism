"use client";

import { useState, useEffect } from "react";

const TZ_OFFSETS: Record<string, number> = {
  IST: 330, AEDT: 660, AEST: 600, GST: 240, BST: 60,
  GMT: 0, UTC: 0, SAST: 120, PKT: 300, SLT: 330, AST: -240,
};

interface LocalTimeProps {
  date: string;    // "2026-03-28"
  time: string;    // "19:30 IST"
  className?: string;
}

export function LocalTime({ date, time, className }: LocalTimeProps) {
  const [localStr, setLocalStr] = useState<string | null>(null);

  useEffect(() => {
    const parts = time.trim().split(/\s+/);
    const timePart = parts[0];
    const tzCode = parts[1] || "IST";
    const [hours, minutes] = timePart.split(":").map(Number);
    const offsetMinutes = TZ_OFFSETS[tzCode] ?? 330;

    const utcMs =
      Date.UTC(
        Number(date.split("-")[0]),
        Number(date.split("-")[1]) - 1,
        Number(date.split("-")[2]),
        hours,
        minutes,
        0
      ) - offsetMinutes * 60 * 1000;

    const localDate = new Date(utcMs);

    // Check if user is already in the same timezone as the match
    const userOffset = -localDate.getTimezoneOffset(); // in minutes, positive east
    if (userOffset === offsetMinutes) {
      setLocalStr(null); // same timezone, don't show duplicate
      return;
    }

    const localTime = localDate.toLocaleTimeString(undefined, {
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    });
    const localDateStr = localDate.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
    });

    // Check if date changed (e.g., IST evening = previous day in US)
    const matchDay = Number(date.split("-")[2]);
    const localDay = localDate.getDate();
    const dateNote = localDay !== matchDay ? `, ${localDateStr}` : "";

    setLocalStr(`${localTime}${dateNote} your time`);
  }, [date, time]);

  if (!localStr) return null;

  return (
    <span className={className ?? "text-[12px] text-outline/70"}>
      ({localStr})
    </span>
  );
}
