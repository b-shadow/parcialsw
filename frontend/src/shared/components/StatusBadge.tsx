import { cn } from "../utils/cn";

export type StatusBadgeTone =
  | "neutral"
  | "success"
  | "warning"
  | "danger"
  | "info"
  | "ai";

type StatusBadgeProps = {
  children: string;
  tone?: StatusBadgeTone;
  dot?: boolean;
};

const tones: Record<StatusBadgeTone, string> = {
  neutral: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
  success: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300",
  warning: "bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300",
  danger: "bg-rose-50 text-rose-700 dark:bg-rose-950/50 dark:text-rose-300",
  info: "bg-sky-50 text-sky-700 dark:bg-sky-950/50 dark:text-sky-300",
  ai: "bg-teal-50 text-teal-700 dark:bg-teal-950/50 dark:text-teal-300",
};

const dotColors: Record<StatusBadgeTone, string> = {
  neutral: "bg-slate-500",
  success: "bg-emerald-500",
  warning: "bg-amber-500",
  danger: "bg-rose-500",
  info: "bg-sky-500",
  ai: "bg-teal-500",
};

export function StatusBadge({
  children,
  tone = "neutral",
  dot = false,
}: StatusBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium",
        tones[tone]
      )}
    >
      {dot && <span className={cn("h-1.5 w-1.5 rounded-full", dotColors[tone])} />}
      {children}
    </span>
  );
}
