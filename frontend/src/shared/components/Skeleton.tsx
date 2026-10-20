import { cn } from "../utils/cn";

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "motion-safe:animate-pulse rounded bg-slate-200 dark:bg-slate-800",
        className
      )}
      aria-hidden="true"
    />
  );
}
