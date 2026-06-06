import type { ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
  variant?: "default" | "flat" | "elevated";
  hover?: boolean;
}

const variants = {
  default: "border border-slate-200/80 bg-white shadow-card",
  flat: "border border-slate-200/60 bg-white",
  elevated: "border border-slate-200/60 bg-white shadow-card-lg",
};

export function Card({
  children,
  className = "",
  variant = "default",
  hover = false,
}: CardProps) {
  return (
    <div
      className={`rounded-xl p-5 ${variants[variant]} ${
        hover
          ? "cursor-pointer transition-shadow duration-200 hover:shadow-card-hover hover:-translate-y-px"
          : "transition-shadow duration-200"
      } ${className}`}
    >
      {children}
    </div>
  );
}
