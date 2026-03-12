import type { Event } from "../types/event";

function formatRelativeDate(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffDays = Math.floor((date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
  const time = date.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });

  if (diffDays < 0) return date.toLocaleDateString("en-US", { month: "short", day: "numeric" }) + ` · ${time}`;
  if (diffDays === 0) return `Today · ${time}`;
  if (diffDays === 1) return `Tomorrow · ${time}`;
  if (diffDays < 7) return date.toLocaleDateString("en-US", { weekday: "long" }) + ` · ${time}`;
  return date.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" }) + ` · ${time}`;
}

function formatSources(source: string): string {
  return source
    .split(",")
    .map((s) => s.trim().replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()))
    .join(", ");
}

export default function EventCard({ event }: { event: Event }) {
  const catClass = event.category ? `cat-${event.category}` : "";
  const scorePercent = Math.round(event.score * 100);

  return (
    <article className="event-card">
      <div className="event-card-top">
        <div className="event-card-badges">
          {event.emoji && (
            <span className="event-emoji">{event.emoji}</span>
          )}
          {event.category && (
            <span className={`event-category ${catClass}`}>
              {event.category}
            </span>
          )}
        </div>
        <span className="event-sources-count">
          {event.source_count > 1
            ? `${event.source_count} sources`
            : "1 source"}
        </span>
      </div>

      <h3 className="event-title">{event.title}</h3>

      {event.vibe && (
        <p className="event-vibe">{event.vibe}</p>
      )}

      <p className="event-date">{formatRelativeDate(event.date)}</p>

      {event.venue && <p className="event-venue">{event.venue}</p>}

      {event.description && (
        <p className="event-desc">{event.description}</p>
      )}

      <div className="score-bar">
        <div className="score-fill" style={{ width: `${scorePercent}%` }} />
      </div>

      <div className="event-footer">
        <span className="event-source-label">
          {formatSources(event.source)}
        </span>
        {event.source_url && (
          <a
            href={event.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="event-link"
          >
            View →
          </a>
        )}
      </div>
    </article>
  );
}
