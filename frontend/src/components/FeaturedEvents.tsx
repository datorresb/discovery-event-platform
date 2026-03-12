import { useRef } from "react";
import type { Event } from "../types/event";

function formatShortDate(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffDays = Math.floor((date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Tomorrow";
  if (diffDays < 7) return date.toLocaleDateString("en-US", { weekday: "short" });
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function getTierInfo(score: number, sourceCount: number): { label: string; cls: string } {
  if (sourceCount >= 2 || score >= 0.75) return { label: "Trending", cls: "tier-trending" };
  if (score >= 0.4) return { label: "Notable", cls: "tier-notable" };
  return { label: "Discover", cls: "tier-discover" };
}

export default function FeaturedEvents({ events }: { events: Event[] }) {
  const scrollRef = useRef<HTMLDivElement>(null);

  if (events.length === 0) return null;

  const scroll = (dir: number) => {
    scrollRef.current?.scrollBy({ left: dir * 280, behavior: "smooth" });
  };

  return (
    <section className="featured-section">
      <div className="featured-header">
        <h2 className="section-title">This Week</h2>
        <div className="carousel-nav">
          <button className="carousel-btn" onClick={() => scroll(-1)} aria-label="Scroll left">←</button>
          <button className="carousel-btn" onClick={() => scroll(1)} aria-label="Scroll right">→</button>
        </div>
      </div>
      <div className="carousel-track" ref={scrollRef}>
        {events.map((event, i) => {
          const tier = getTierInfo(event.score, event.source_count);
          const Tag = event.source_url ? "a" : "div";
          const linkProps = event.source_url
            ? { href: event.source_url, target: "_blank" as const, rel: "noopener noreferrer" }
            : {};
          return (
            <Tag key={event.id} className="carousel-card" {...linkProps}>
              <div className="carousel-card-top">
                <span className="carousel-rank">
                  {event.emoji || `#${i + 1}`}
                </span>
                <span className={`tier-badge ${tier.cls}`}>{tier.label}</span>
              </div>
              <h3 className="carousel-title">{event.title}</h3>
              {event.vibe && <p className="carousel-vibe">{event.vibe}</p>}
              <div className="carousel-card-bottom">
                <span className="carousel-date">{formatShortDate(event.date)}</span>
                {event.venue && <span className="carousel-venue">{event.venue}</span>}
              </div>
            </Tag>
          );
        })}
      </div>
    </section>
  );
}
