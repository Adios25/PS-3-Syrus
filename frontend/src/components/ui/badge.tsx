import * as React from "react";
import { cn } from "@/lib/utils";

type BadgeVariant = "default" | "secondary" | "outline" | "success" | "warning" | "destructive";

const badgeStyles: Record<BadgeVariant, string> = {
  default: "bg-slate-950 text-white",
  secondary: "bg-teal-50 text-teal-800 ring-1 ring-inset ring-teal-200",
  outline: "bg-white text-slate-700 ring-1 ring-inset ring-slate-300",
  success: "bg-emerald-50 text-emerald-800 ring-1 ring-inset ring-emerald-200",
  warning: "bg-amber-50 text-amber-800 ring-1 ring-inset ring-amber-200",
  destructive: "bg-rose-50 text-rose-800 ring-1 ring-inset ring-rose-200",
};

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: BadgeVariant;
}

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <div
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.16em]",
        badgeStyles[variant],
        className,
      )}
      {...props}
    />
  );
}

export { Badge };
