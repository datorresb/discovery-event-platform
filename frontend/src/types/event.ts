export interface Event {
  id: number;
  title: string;
  date: string;
  venue: string | null;
  location: string;
  category: string | null;
  description: string | null;
  source: string;
  source_url: string | null;
  source_count: number;
  score: number;
  emoji: string | null;
  color_tag: string | null;
  vibe: string | null;
}
