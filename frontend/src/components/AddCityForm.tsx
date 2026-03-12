import { useEffect, useRef, useState } from "react";
import { generateCity } from "../api/events";

interface AddCityFormProps {
  onCityAdded: (city: string) => void;
}

const PROGRESS_STEPS = [
  "Searching event sources",
  "Cross-referencing events",
  "Scoring & ranking",
];

export default function AddCityForm({ onCityAdded }: AddCityFormProps) {
  const [city, setCity] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [step, setStep] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval>>();

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = city.trim();
    if (!trimmed) return;

    setLoading(true);
    setError(null);
    setStep(0);

    // Simulate progress steps while waiting for the API
    timerRef.current = setInterval(() => {
      setStep((prev) => Math.min(prev + 1, PROGRESS_STEPS.length - 1));
    }, 4000);

    try {
      await generateCity(trimmed);
      onCityAdded(trimmed);
      setCity("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate events");
    } finally {
      setLoading(false);
      if (timerRef.current) clearInterval(timerRef.current);
    }
  };

  return (
    <div className="add-city">
      <div className="filter-label">Add City</div>
      <form onSubmit={handleSubmit} className="add-city-form">
        <input
          type="text"
          value={city}
          onChange={(e) => setCity(e.target.value)}
          placeholder="Any city..."
          disabled={loading}
          className="add-city-input"
        />
        <button
          type="submit"
          disabled={loading || !city.trim()}
          className="add-city-btn"
        >
          {loading ? "Discovering..." : "Discover"}
        </button>
      </form>

      {loading && (
        <div className="gen-progress">
          <div className="gen-progress-title">
            Discovering events in {city}
          </div>
          {PROGRESS_STEPS.map((label, i) => (
            <div
              key={label}
              className={`gen-step ${i < step ? "done" : i === step ? "active" : ""}`}
            >
              {i < step ? "✓" : i === step ? <span className="spinner" /> : "○"}
              {label}
            </div>
          ))}
        </div>
      )}

      {error && (
        <p className="add-city-status error">{error}</p>
      )}
    </div>
  );
}
