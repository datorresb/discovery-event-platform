import type { Event } from "../types/event";
import EventCard from "./EventCard";

interface EventGridProps {
  events: Event[];
  loading: boolean;
}

function SkeletonCard() {
  return (
    <div className="skeleton-card">
      <div className="skeleton skeleton-line w-40" />
      <div className="skeleton skeleton-line w-80" />
      <div className="skeleton skeleton-line w-60" />
      <div className="skeleton skeleton-line w-80" style={{ marginTop: 16 }} />
      <div className="skeleton skeleton-line w-40" style={{ marginTop: 24 }} />
    </div>
  );
}

export default function EventGrid({ events, loading }: EventGridProps) {
  if (loading) {
    return (
      <div className="event-grid">
        {Array.from({ length: 6 }, (_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    );
  }

  if (events.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">◇</div>
        <h3 className="empty-state-title">No events found</h3>
        <p className="empty-state-text">
          Try a different filter, or add a new city to discover events.
        </p>
      </div>
    );
  }

  return (
    <div className="event-grid">
      {events.map((event) => (
        <EventCard key={event.id} event={event} />
      ))}
    </div>
  );
}
