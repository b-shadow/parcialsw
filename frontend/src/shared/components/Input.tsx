import type { InputHTMLAttributes } from "react";

import { cn } from "../utils/cn";

type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
};

export function Input({ className, label, id, ...props }: InputProps) {
  const fieldId = id ?? props.name ?? label;
  return (
    <label className="grid gap-1.5 text-sm font-medium text-slate-700 dark:text-slate-200" htmlFor={fieldId}>
      {label}
      <input
        id={fieldId}
        className={cn(
          "h-10 rounded-md border border-slate-300 bg-white px-3 text-sm text-ink outline-none transition placeholder:text-slate-400 focus:border-accent focus:ring-2 focus:ring-teal-100 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100 dark:placeholder:text-slate-500 dark:focus:ring-teal-900/50",
          className
        )}
        {...props}
      />
    </label>
  );
}
