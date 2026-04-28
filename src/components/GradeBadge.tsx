import type { Grade } from "@/lib/types";

const gradeStyles: Record<Grade, { text: string; bg: string }> = {
  "A+": { text: "text-grade-aplus", bg: "bg-grade-aplus/10" },
  A: { text: "text-grade-a", bg: "bg-grade-a/10" },
  B: { text: "text-grade-b", bg: "bg-grade-b/10" },
  C: { text: "text-grade-c", bg: "bg-grade-c/10" },
  D: { text: "text-grade-d", bg: "bg-grade-d/10" },
};

interface GradeBadgeProps {
  grade: Grade;
  size?: "sm" | "md" | "lg" | "xl";
}

export function GradeBadge({ grade, size = "md" }: GradeBadgeProps) {
  const style = gradeStyles[grade];
  const sizeClass = {
    sm: "text-sm px-2 py-0.5",
    md: "text-xl px-3 py-1",
    lg: "text-2xl px-4 py-1.5",
    xl: "text-7xl",
  }[size];

  if (size === "xl") {
    return (
      <span className={`font-headline font-black ${style.text} ${sizeClass}`}>
        {grade}
      </span>
    );
  }

  return (
    <span
      className={`font-headline font-black rounded-lg ${style.bg} ${style.text} ${sizeClass}`}
    >
      {grade}
    </span>
  );
}
