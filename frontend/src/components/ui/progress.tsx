import { cn } from "@/lib/utils";

interface ProgressProps {
  value?: number;
  className?: string;
  indicatorClassName?: string;
}

export function Progress({ value = 0, className, indicatorClassName }: ProgressProps) {
  const clamped = Math.max(0, Math.min(100, value));

  return (
    <div className={cn("h-2.5 w-full overflow-hidden rounded-full bg-slate-200", className)}>
      <div
        className={cn(
          "h-full rounded-full bg-gradient-to-r from-teal-500 via-cyan-500 to-sky-500 transition-all duration-500 ease-out",
          indicatorClassName,
        )}
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}
