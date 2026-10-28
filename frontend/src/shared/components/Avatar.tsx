import { Bot } from "lucide-react";
import { cn } from "../utils/cn";

export type AvatarProps = {
  name: string;
  userId?: string;
  kind?: "user" | "ai";
  size?: "sm" | "md";
};

const COLOR_CLASSES = [
  "bg-teal-700 text-white",
  "bg-blue-600 text-white",
  "bg-purple-600 text-white",
  "bg-rose-600 text-white",
  "bg-amber-600 text-white",
  "bg-sky-700 text-white",
];

function getHashColor(userId?: string): string {
  if (!userId) return COLOR_CLASSES[0];
  let hash = 0;
  for (let i = 0; i < userId.length; i++) {
    hash = (hash << 5) - hash + userId.charCodeAt(i);
    hash |= 0;
  }
  const index = Math.abs(hash) % COLOR_CLASSES.length;
  return COLOR_CLASSES[index];
}

function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "U";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[1][0]).toUpperCase();
}

export function Avatar({ name, userId, kind = "user", size = "md" }: AvatarProps) {
  const sizeClasses =
    size === "sm" ? "h-7 w-7 text-xs" : "h-9 w-9 text-sm font-semibold";

  if (kind === "ai") {
    return (
      <div
        className={cn(
          "inline-flex shrink-0 items-center justify-center rounded-full bg-teal-100 text-teal-800 ring-2 ring-white dark:bg-teal-950 dark:text-teal-300 dark:ring-slate-900",
          sizeClasses
        )}
        title={name || "Asistente IA"}
        aria-label={name || "Asistente IA"}
      >
        <Bot size={size === "sm" ? 14 : 18} />
      </div>
    );
  }

  const colorClass = getHashColor(userId);

  return (
    <div
      className={cn(
        "inline-flex shrink-0 items-center justify-center rounded-full font-medium ring-2 ring-white dark:ring-slate-900",
        sizeClasses,
        colorClass
      )}
      title={name}
      aria-label={name}
    >
      {getInitials(name)}
    </div>
  );
}

export function PresenceStack({
  people,
  max = 4,
}: {
  people: { id: string; name: string; kind?: "user" | "ai" }[];
  max?: number;
}): React.ReactNode {
  const visible = people.slice(0, max);
  const remaining = people.length - max;

  return (
    <div className="flex items-center -space-x-2">
      {visible.map((person) => (
        <Avatar
          key={person.id}
          name={person.name}
          userId={person.id}
          kind={person.kind}
          size="sm"
        />
      ))}
      {remaining > 0 && (
        <span
          className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-slate-200 text-xs font-bold text-slate-700 ring-2 ring-white dark:bg-slate-700 dark:text-slate-200 dark:ring-slate-900"
          title={`+${remaining} más`}
        >
          +{remaining}
        </span>
      )}
    </div>
  );
}
