import type { ReactNode } from "react";

type CardProps = {
  children: ReactNode;
  className?: string;
};

export function Card({
  children,
  className = "",
}: CardProps) {
  return (
    <section
      className={[
        "rounded-3xl border border-slate-800",
        "bg-slate-900 p-6",
        "shadow-lg shadow-black/10",
        className,
      ].join(" ")}
    >
      {children}
    </section>
  );
}