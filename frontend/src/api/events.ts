import type { Event } from "../types/event";

const API_BASE = "/api";

export async function fetchEvents(params?: {
  category?: string;
  location?: string;
  sort?: string;
  date_from?: string;
  date_to?: string;
}): Promise<Event[]> {
  const url = new URL(`${API_BASE}/events`, window.location.origin);
  if (params?.category) url.searchParams.set("category", params.category);
  if (params?.location) url.searchParams.set("location", params.location);
  if (params?.sort) url.searchParams.set("sort", params.sort);
  if (params?.date_from) url.searchParams.set("date_from", params.date_from);
  if (params?.date_to) url.searchParams.set("date_to", params.date_to);

  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function fetchTopEvents(limit = 5, location?: string): Promise<Event[]> {
  const url = new URL(`${API_BASE}/events/top`, window.location.origin);
  url.searchParams.set("limit", String(limit));
  if (location) url.searchParams.set("location", location);
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function fetchCities(): Promise<string[]> {
  const res = await fetch(`${API_BASE}/cities`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function generateCity(city: string): Promise<Event[]> {
  const res = await fetch(`${API_BASE}/cities/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ city }),
  });
  if (res.status === 409) {
    throw new Error("City already exists");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Generation failed" }));
    throw new Error(err.detail || "Generation failed");
  }
  return res.json();
}
