import type { HTMLAttributes } from "react";

import { cn } from "../utils/cn";

export function Panel({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("rounded-md border border-slate-200 bg-white", className)} {...props} />;
}
