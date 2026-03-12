const CATEGORIES = [
  { key: "all", label: "All Events" },
  { key: "music", label: "Music" },
  { key: "culture", label: "Culture" },
  { key: "food", label: "Food & Drink" },
  { key: "nightlife", label: "Nightlife" },
  { key: "community", label: "Community" },
];

function toDateStr(d: Date): string {
  return d.toISOString().slice(0, 10);
}

const DATE_RANGES = [
  { key: "all", label: "Any Date" },
  { key: "today", label: "Today" },
  { key: "week", label: "This Week" },
  { key: "month", label: "This Month" },
  { key: "pick", label: "Pick Week..." },
];

function getDateRange(key: string): { from?: string; to?: string } {
  const now = new Date();
  if (key === "today") {
    const d = toDateStr(now);
    return { from: d, to: d };
  }
  if (key === "week") {
    const end = new Date(now);
    end.setDate(end.getDate() + 7);
    return { from: toDateStr(now), to: toDateStr(end) };
  }
  if (key === "month") {
    const end = new Date(now);
    end.setDate(end.getDate() + 30);
    return { from: toDateStr(now), to: toDateStr(end) };
  }
  return {};
}

interface FilterSidebarProps {
  selected: string;
  onSelect: (category: string) => void;
  dateRange: string;
  onDateRange: (range: string, from?: string, to?: string) => void;
}

export default function FilterSidebar({ selected, onSelect, dateRange, onDateRange }: FilterSidebarProps) {
  return (
    <>
      <div className="filter-section">
        <div className="filter-label">Category</div>
        <div className="filter-list">
          {CATEGORIES.map((cat) => (
            <button
              key={cat.key}
              onClick={() => onSelect(cat.key)}
              className="filter-item"
              data-active={selected === cat.key}
            >
              {cat.label}
            </button>
          ))}
        </div>
      </div>
      <div className="filter-section">
        <div className="filter-label">When</div>
        <div className="filter-list">
          {DATE_RANGES.map((dr) => (
            <button
              key={dr.key}
              onClick={() => {
                if (dr.key === "pick") {
                  // Just activate the picker, don't set dates yet
                  onDateRange("pick");
                  return;
                }
                const range = getDateRange(dr.key);
                onDateRange(dr.key, range.from, range.to);
              }}
              className="filter-item"
              data-active={dateRange === dr.key}
            >
              {dr.label}
            </button>
          ))}
        </div>
        {dateRange === "pick" && (
          <div className="date-picker-row">
            <input
              type="date"
              className="date-input"
              onChange={(e) => {
                if (!e.target.value) return;
                const from = e.target.value;
                const end = new Date(from);
                end.setDate(end.getDate() + 6);
                onDateRange("pick", from, toDateStr(end));
              }}
            />
            <span className="date-hint">7-day window</span>
          </div>
        )}
      </div>
    </>
  );
}
