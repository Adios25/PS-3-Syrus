import * as React from "react";
import { cn } from "@/lib/utils";

type ButtonVariant = "default" | "secondary" | "outline" | "ghost" | "success";
type ButtonSize = "default" | "sm" | "lg" | "icon";

const variantStyles: Record<ButtonVariant, string> = {
  default:
    "bg-slate-950 text-white shadow-[0_18px_40px_-22px_rgba(15,23,42,0.8)] hover:bg-slate-800",
  secondary:
    "bg-teal-700 text-white shadow-[0_18px_40px_-22px_rgba(15,118,110,0.6)] hover:bg-teal-600",
  outline:
    "border border-slate-300 bg-white/90 text-slate-900 hover:border-slate-400 hover:bg-white",
  ghost: "text-slate-700 hover:bg-slate-100 hover:text-slate-950",
  success:
    "bg-emerald-600 text-white shadow-[0_18px_40px_-22px_rgba(5,150,105,0.7)] hover:bg-emerald-500",
};

const sizeStyles: Record<ButtonSize, string> = {
  default: "h-10 px-4 py-2",
  sm: "h-8 rounded-xl px-3 text-xs",
  lg: "h-11 rounded-2xl px-5",
  icon: "h-10 w-10",
};

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", type = "button", ...props }, ref) => (
    <button
      ref={ref}
      type={type}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-2xl text-sm font-medium transition disabled:pointer-events-none disabled:opacity-50",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400 focus-visible:ring-offset-2",
        variantStyles[variant],
        sizeStyles[size],
        className,
      )}
      {...props}
    />
  ),
);

Button.displayName = "Button";

export { Button };
