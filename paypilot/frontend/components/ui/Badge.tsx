import { cn } from "@/lib/utils";

export function Badge({
  children,
  tone = "neutral",
  className,
}: {
  children: React.ReactNode;
  tone?: "neutral" | "good" | "warn" | "bad" | "info";
  className?: string;
}) {
  const tones = {
    neutral: "bg-mist-100 text-ink-700",
    good: "bg-gain-400/15 text-gain-500",
    warn: "bg-warn-400/15 text-warn-500",
    bad: "bg-danger-400/15 text-danger-500",
    info: "bg-accent-400/15 text-accent-600",
  };
  return (
    <span className={cn("inline-flex items-center rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide", tones[tone], className)}>
      {children}
    </span>
  );
}
