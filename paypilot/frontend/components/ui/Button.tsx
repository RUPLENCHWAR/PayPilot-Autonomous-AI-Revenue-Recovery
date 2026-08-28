import { cn } from "@/lib/utils";

export function Button({
  children,
  className,
  variant = "primary",
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost" | "danger";
}) {
  const styles = {
    primary: "bg-ink-900 text-white hover:bg-ink-800",
    secondary: "bg-white text-ink-900 border border-ink-900/10 hover:bg-mist-50",
    ghost: "bg-transparent text-ink-700 hover:bg-mist-100",
    danger: "bg-danger-500 text-white hover:bg-danger-400",
  };
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-50",
        styles[variant],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}
