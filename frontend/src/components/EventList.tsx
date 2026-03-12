import type { Event } from "../types/event";
import EventCard from "./EventCard";

export default function EventList({ events }: { events: Event[] }) {
  if (events.length === 0) {
    return (
      <div style={{ textAlign: "center", color: "#9ca3af", padding: "3rem 0" }}>
        <p style={{ fontSize: "2rem" }}>🔍</p>
        <p>No events found. Try adding a city above!</p>
      </div>
    );
  }

  return (
    <div style={styles.grid}>
      {events.map((event) => (
        <EventCard key={event.id} event={event} />
      ))}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))",
    gap: "1.25rem",
  },
};
