"use client";

/**
 * FLOW-FE-002: Reusable EmptyState component.
 * Displays when a list has no items.
 *
 * Props:
 *  - icon      : React element (Lucide icon recommended)
 *  - title     : Main heading
 *  - description: Subtext
 *  - actionLabel: Optional CTA button text
 *  - onAction  : Optional CTA handler
 */

import React from "react";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
    icon?: React.ReactNode;
    title: string;
    description?: string;
    actionLabel?: string;
    onAction?: () => void;
    className?: string;
}

export function EmptyState({
    icon,
    title,
    description,
    actionLabel,
    onAction,
    className,
}: EmptyStateProps) {
    return (
        <div
            data-testid="empty-state"
            className={cn(
                "flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 px-6 py-10 text-center",
                className
            )}
        >
            {icon && (
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-400">
                    {icon}
                </div>
            )}

            <p className="text-sm font-semibold text-slate-800">{title}</p>

            {description && (
                <p className="mt-1 max-w-xs text-sm leading-6 text-slate-500">
                    {description}
                </p>
            )}

            {actionLabel && onAction && (
                <button
                    type="button"
                    onClick={onAction}
                    className="mt-4 rounded-full bg-slate-900 px-4 py-2 text-xs font-semibold text-white transition hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2"
                >
                    {actionLabel}
                </button>
            )}
        </div>
    );
}

export default EmptyState;
