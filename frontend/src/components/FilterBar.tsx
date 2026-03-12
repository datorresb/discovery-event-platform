const CATEGORIES = ["all", "music", "culture", "food", "nightlife", "community"];

interface FilterBarProps {
  selected: string;
  onSelect: (category: string) => void;
  city: string;
  cities: string[];
  onCityChange: (city: string) => void;
  sort: string;
  onSortChange: (sort: string) => void;
}

export default function FilterBar({ selected, onSelect, city, cities, onCityChange, sort, onSortChange }: FilterBarProps) {
  return (
    <div style={styles.bar}>
      <div style={styles.categories}>
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            onClick={() => onSelect(cat)}
            style={{
              ...styles.chip,
              ...(selected === cat ? styles.chipActive : {}),
            }}
          >
            {cat === "all" ? "All" : cat.charAt(0).toUpperCase() + cat.slice(1)}
          </button>
        ))}
      </div>
      <div style={styles.controls}>
        <select
          value={city}
          onChange={(e) => onCityChange(e.target.value)}
          style={styles.sortSelect}
        >
          <option value="All Cities">📍 All Cities</option>
          {cities.map((c) => (
            <option key={c} value={c}>
              📍 {c}
            </option>
          ))}
        </select>
        <select
          value={sort}
          onChange={(e) => onSortChange(e.target.value)}
          style={styles.sortSelect}
        >
          <option value="score">🔥 Top Ranked</option>
          <option value="date">📆 By Date</option>
        </select>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  bar: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    flexWrap: "wrap",
    gap: "1rem",
    marginBottom: "1.5rem",
    background: "#ffffff",
    borderRadius: 16,
    padding: "0.75rem 1rem",
    border: "1px solid #e5e7eb",
    boxShadow: "0 1px 2px rgba(0,0,0,0.04)",
  },
  categories: { display: "flex", gap: "0.4rem", flexWrap: "wrap" },
  chip: {
    background: "#f9fafb",
    color: "#6b7280",
    border: "1px solid #e5e7eb",
    borderRadius: 20,
    padding: "6px 16px",
    fontSize: "0.82rem",
    cursor: "pointer",
    transition: "all 0.15s",
    fontWeight: 500,
  },
  chipActive: {
    background: "#6366f1",
    color: "#ffffff",
    borderColor: "#6366f1",
    fontWeight: 700,
  },
  controls: { display: "flex", gap: "0.5rem" },
  sortSelect: {
    background: "#f9fafb",
    color: "#374151",
    border: "1px solid #e5e7eb",
    borderRadius: 10,
    padding: "6px 12px",
    fontSize: "0.82rem",
    cursor: "pointer",
  },
};
