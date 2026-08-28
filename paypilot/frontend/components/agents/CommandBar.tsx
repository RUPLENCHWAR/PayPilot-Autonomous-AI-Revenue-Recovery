"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Search } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { formatINR } from "@/lib/utils";
import type { Opportunity } from "@/lib/types";

type CommandResult = {
  intent: string;
  title: string;
  answer: string;
  requires_confirmation?: boolean;
  data?: { opportunities?: Opportunity[] };
};

export function CommandBar() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<CommandResult | null>(null);
  const [error, setError] = useState("");
  const router = useRouter();

  async function run(confirm = false) {
    if (!query.trim()) return;
    setLoading(true);
    setError("");
    try {
      const data = (await api.command(query, confirm)) as CommandResult;
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Command failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="relative w-full max-w-2xl">
      <div className="flex items-center gap-2 rounded-2xl border border-ink-900/10 bg-white px-3 py-2">
        <Search size={16} className="text-mist-400" />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && run()}
          placeholder="Ask PayPilot — biggest leaks, recoverable revenue, recover highest priority…"
          className="w-full bg-transparent text-sm outline-none placeholder:text-mist-400"
        />
        <Button onClick={() => run()} disabled={loading} className="h-8 px-3 text-xs">
          {loading ? "…" : "Run"}
        </Button>
      </div>
      {error ? <p className="mt-2 text-xs text-danger-500">{error}</p> : null}
      {result ? (
        <div className="absolute z-30 mt-2 w-full rounded-2xl border border-ink-900/10 bg-white p-4 shadow-panel">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="eyebrow">{result.intent}</p>
              <h3 className="mt-1 font-medium">{result.title}</h3>
              <p className="mt-1 text-sm text-ink-700/80">{result.answer}</p>
            </div>
            <button className="text-xs text-mist-400" onClick={() => setResult(null)}>
              Close
            </button>
          </div>
          {result.requires_confirmation ? (
            <Button className="mt-3" onClick={() => run(true)}>
              Confirm financial action
            </Button>
          ) : null}
          {result.data?.opportunities?.length ? (
            <ul className="mt-3 space-y-2">
              {result.data.opportunities.slice(0, 5).map((opp) => (
                <li key={opp.id}>
                  <button
                    className="w-full rounded-xl bg-mist-50 px-3 py-2 text-left text-sm hover:bg-mist-100"
                    onClick={() => {
                      setResult(null);
                      router.push(`/recovery/${opp.id}`);
                    }}
                  >
                    {opp.customer_name} · {formatINR(opp.amount)} · {Math.round(opp.recovery_probability * 100)}%
                  </button>
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
