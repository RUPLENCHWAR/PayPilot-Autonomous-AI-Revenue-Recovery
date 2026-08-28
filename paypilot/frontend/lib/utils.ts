import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatINR(amount: number | null | undefined): string {
  const value = Number(amount || 0);
  const sign = value < 0 ? "-" : "";
  const abs = Math.abs(value);
  const [integer, frac] = abs.toFixed(0).split(".");
  const lastThree = integer.slice(-3);
  const rest = integer.slice(0, -3);
  let grouped = lastThree;
  if (rest) {
    grouped = rest.replace(/\B(?=(\d{2})+(?!\d))/g, ",") + "," + lastThree;
  }
  return `${sign}₹${grouped}`;
}

export function formatPct(value: number | null | undefined): string {
  return `${Math.round(Number(value || 0) * 100)}%`;
}

export function formatDate(value: string): string {
  return new Date(value).toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
