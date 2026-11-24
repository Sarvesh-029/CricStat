import type { ReactNode } from "react";

export default function Card({ title, children, className = "" }: { title?: string; children: ReactNode; className?: string }) {
  return (
    <div className={`bg-card border border-slate-800 rounded-xl p-5 ${className}`}>
      {title && <div className="text-sm text-slate-400 mb-2">{title}</div>}
      {children}
    </div>
  );
}