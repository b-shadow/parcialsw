import type { TextareaHTMLAttributes } from "react";

import { cn } from "../utils/cn";

type TextareaProps = TextareaHTMLAttributes<HTMLTextAreaElement> & {
  label: string;
};

export function Textarea({ className, label, id, ...props }: TextareaProps) {
  const fieldId = id ?? props.name ?? label;
  return (
    <label className="grid gap-1.5 text-sm font-medium text-slate-700" htmlFor={fieldId}>
      {label}
      <textarea
        id={fieldId}
        className={cn(
          "min-h-24 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink outline-none transition placeholder:text-slate-400 focus:border-accent focus:ring-2 focus:ring-teal-100",
          className
        )}
        {...props}
      />
    </label>
  );
}
