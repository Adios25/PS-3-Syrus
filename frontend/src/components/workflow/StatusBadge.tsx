"use client";

/**
 * FLOW-FE-001: Enhanced StatusBadge component.
 * Supports 6 workflow states: active, inactive, draft, running, failed, archived.
 */

import React from "react";
import { cn } from "@/lib/utils";

export type WorkflowStatus =
  | "active"
  | "inactive"
  | "draft"
  | "running"
  | "failed"
  | "archived";

interface StatusBadgeProps {
  status: WorkflowStatus;
  className?: string;
}

const STATUS_CONFIG: Record<
  WorkflowStatus,
  { label: string; classes: string; textClass?: string; pulse?: boolean }
> = {
  active: {
    label: "Active",
    classes:
      "bg-emerald-100 text-emerald-800 border-emerald-200",
  },
  inactive: {
    label: "Inactive",
    classes: "bg-slate-100 text-slate-600 border-slate-200",
  },
  draft: {
    label: "Draft",
    classes: "bg-yellow-100 text-yellow-800 border-yellow-200",
  },
  running: {
    label: "Running",
    classes: "bg-blue-100 text-blue-800 border-blue-200",
    pulse: true,
  },
  failed: {
    label: "Failed",
    classes: "bg-rose-100 text-rose-800 border-rose-200",
  },
  archived: {
    label: "Archived",
    classes: "bg-slate-100 text-slate-500 border-slate-200",
    textClass: "line-through",
  },
};

/**
 * Renders a coloured status badge for a workflow item.
 *
 * @example
 * <StatusBadge status="running" />
 * <StatusBadge status="failed" />
 */
export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = STATUS_CONFIG[status];

  return (
    <span
      data-testid={`status-badge-${status}`}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium",
        config.classes,
        className
      )}
    >
      {/* Pulse dot for Running state */}
      {config.pulse && (
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-blue-500 opacity-75" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-blue-600" />
        </span>
      )}
      <span className={config.textClass}>{config.label}</span>
    </span>
  );
}

export default StatusBadge;
