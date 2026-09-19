import type { InputHTMLAttributes } from "react";

import { cn } from "../utils/cn";

type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
};

export function Input({ className, label, id, ...props }: InputProps) {
  const fieldId = id ?? props.name ?? label;
  return (
    <label className="grid gap-1.5 text-sm font-medium text-slate-700" htmlFor={fieldId}>
      {label}
      <input
        id={fieldId}
        className={cn(
          "h-10 rounded-md border border-slate-300 bg-white px-3 text-sm text-ink outline-none transition placeholder:text-slate-400 focus:border-accent focus:ring-2 focus:ring-teal-100",
          className
        )}
        {...props}
      />
    </label>
  );
}
