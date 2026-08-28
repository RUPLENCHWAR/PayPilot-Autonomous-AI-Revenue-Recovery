"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import {
  Activity,
  LayoutDashboard,
  Receipt,
  ShieldCheck,
  Settings,
  Users,
  Wallet,
  SlidersHorizontal,
} from "lucide-react";
import { api } from "@/lib/api";
import type { AppSettings } from "@/lib/types";
import { CommandBar } from "@/components/agents/CommandBar";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/transactions", label: "Transactions", icon: Receipt },
  { href: "/recovery", label: "Recovery Center", icon: Wallet },
  { href: "/customers", label: "Customers", icon: Users },
  { href: "/agents", label: "Agent Activity", icon: Activity },
  { href: "/simulator", label: "Recovery Simulator", icon: SlidersHorizontal },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [settings, setSettings] = useState<AppSettings | null>(null);

  useEffect(() => {
    api.settings().then((d) => setSettings(d as AppSettings)).catch(() => setSettings(null));
  }, []);

  const mode = settings?.razorpay_mode || "demo";

  return (
    <div className="min-h-screen">
      <aside className="fixed inset-y-0 left-0 z-20 hidden w-64 border-r border-ink-900/5 bg-ink-950 text-white lg:flex lg:flex-col">
        <div className="px-6 py-6">
          <p className="text-[11px] uppercase tracking-[0.22em] text-white/40">PayPilot</p>
          <h1 className="mt-1 font-display text-2xl">Revenue recovery</h1>
          <p className="mt-2 text-xs leading-5 text-white/50">Autonomous AI agent for failed, abandoned, and recoverable payments.</p>
        </div>
        <nav className="flex-1 space-y-1 px-3">
          {NAV.map((item) => {
            const active = pathname === item.href || pathname.startsWith(item.href + "/");
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition",
                  active ? "bg-white/10 text-white" : "text-white/60 hover:bg-white/5 hover:text-white",
                )}
              >
                <Icon size={16} />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="p-4">
          <div className="rounded-2xl bg-white/5 p-4 text-xs text-white/70">
            <div className="flex items-center gap-2 font-medium text-white">
              <ShieldCheck size={14} /> RecoveryGuard
            </div>
            <p className="mt-2 leading-5">Low-risk actions ≤ ₹10,000 may auto-execute. Larger or high-risk actions wait for a human.</p>
          </div>
        </div>
      </aside>
      <div className="lg:pl-64">
        <header className="sticky top-0 z-10 border-b border-ink-900/5 bg-white/85 backdrop-blur">
          <div className="flex flex-col gap-3 px-4 py-3 md:flex-row md:items-center md:px-8">
            <CommandBar />
            <div className="flex items-center gap-2 md:ml-auto">
              <span className={cn("rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-wide", mode === "demo" ? "bg-warn-400/15 text-warn-500" : "bg-accent-400/15 text-accent-600")}>
                {mode === "demo" ? "Demo Mode" : "Razorpay Test Mode"}
              </span>
              <span className="rounded-full bg-mist-100 px-3 py-1 text-[11px] font-semibold uppercase tracking-wide text-ink-700">
                {settings?.ai_mode === "openai" ? "OpenAI" : "Local engine"}
              </span>
            </div>
          </div>
          <div className="flex gap-1 overflow-x-auto px-4 pb-3 lg:hidden">
            {NAV.map((item) => (
              <Link key={item.href} href={item.href} className="whitespace-nowrap rounded-full bg-mist-100 px-3 py-1 text-xs text-ink-700">
                {item.label}
              </Link>
            ))}
          </div>
        </header>
        <main className="px-4 py-6 md:px-8 md:py-8">{children}</main>
      </div>
    </div>
  );
}
