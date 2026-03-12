import type { Event } from "../types/event";

export default function TopEvents({ events }: { events: Event[] }) {
  if (events.length === 0) return null;

  return (
    <div style={styles.container}>
      <h2 style={styles.heading}>🏆 Top Events This Week</h2>
      <div style={styles.list}>
        {events.map((event, i) => (
          <div key={event.id} style={styles.item}>
            <span style={{
              ...styles.rank,
              background: i === 0 ? "#fef3c7" : i === 1 ? "#f3f4f6" : i === 2 ? "#fef3c7" : "#f9fafb",
              color: i === 0 ? "#d97706" : i === 1 ? "#6b7280" : "#92400e",
            }}>
              #{i + 1}
            </span>
            <div style={styles.details}>
              <span style={styles.title}>{event.title}</span>
              <span style={styles.meta}>
                📍 {event.location} · {event.venue ?? ""} · {event.source_count} source{event.source_count > 1 ? "s" : ""}
              </span>
            </div>
            <span style={styles.score}>{Math.round(event.score * 100)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    background: "linear-gradient(135deg, #f0f9ff 0%, #ede9fe 50%, #fce7f3 100%)",
    border: "1px solid #e0e7ff",
    borderRadius: 20,
    padding: "1.5rem",
    marginBottom: "1.5rem",
  },
  heading: {
    color: "#4f46e5",
    fontSize: "1.15rem",
    fontWeight: 800,
    margin: "0 0 1rem",
  },
  list: { display: "flex", flexDirection: "column", gap: "0.6rem" },
  item: {
    display: "flex",
    alignItems: "center",
    gap: "0.75rem",
    background: "rgba(255,255,255,0.7)",
    borderRadius: 12,
    padding: "0.6rem 0.75rem",
  },
  rank: {
    fontWeight: 800,
    fontSize: "0.85rem",
    minWidth: 32,
    height: 32,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 8,
  },
  details: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    gap: "0.15rem",
  },
  title: { color: "#111827", fontWeight: 700, fontSize: "0.92rem" },
  meta: { color: "#9ca3af", fontSize: "0.75rem" },
  score: {
    color: "#6366f1",
    fontWeight: 800,
    fontSize: "0.9rem",
  },
};
