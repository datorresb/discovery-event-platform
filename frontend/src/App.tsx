import { useEffect, useState } from "react";
import { fetchEvents, fetchTopEvents, fetchCities } from "./api/events";
import AddCityForm from "./components/AddCityForm";
import EventGrid from "./components/EventGrid";
import FilterSidebar from "./components/FilterSidebar";
import FeaturedEvents from "./components/FeaturedEvents";
import type { Event } from "./types/event";

export default function App() {
  const [events, setEvents] = useState<Event[]>([]);
  const [topEvents, setTopEvents] = useState<Event[]>([]);
  const [cities, setCities] = useState<string[]>([]);
  const [category, setCategory] = useState("all");
  const [city, setCity] = useState("All Cities");
  const [sort, setSort] = useState("score");
  const [dateRange, setDateRange] = useState("all");
  const [dateFrom, setDateFrom] = useState<string | undefined>();
  const [dateTo, setDateTo] = useState<string | undefined>();
  const [loading, setLoading] = useState(true);

  const locationParam = city === "All Cities" ? undefined : city;

  useEffect(() => {
    fetchCities().then(setCities).catch(console.error);
  }, []);

  useEffect(() => {
    fetchTopEvents(10, locationParam).then(setTopEvents).catch(console.error);
  }, [city]);

  useEffect(() => {
    setLoading(true);
    fetchEvents({
      category: category === "all" ? undefined : category,
      location: locationParam,
      sort,
      date_from: dateFrom,
      date_to: dateTo,
    })
      .then(setEvents)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [category, city, sort, dateFrom, dateTo]);

  const handleCityAdded = (newCity: string) => {
    fetchCities().then((updated) => {
      setCities(updated);
      setCity(newCity);
    });
  };

  const subtitle = city === "All Cities"
    ? "Curated events from multiple sources"
    : `Events in ${city}`;

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <div className="logo">
            Discovery<span className="logo-dot">.</span>
          </div>

          <div className="header-controls">
            <select
              value={city}
              onChange={(e) => setCity(e.target.value)}
              className="city-select"
            >
              <option value="All Cities">All Cities</option>
              {cities.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>

            <select
              value={sort}
              onChange={(e) => setSort(e.target.value)}
              className="sort-select"
            >
              <option value="score">Top Ranked</option>
              <option value="date">By Date</option>
            </select>
          </div>
        </div>
      </header>

      <div className="main-layout">
        <aside className="sidebar">
          <FilterSidebar
            selected={category}
            onSelect={setCategory}
            dateRange={dateRange}
            onDateRange={(range, from, to) => {
              setDateRange(range);
              setDateFrom(from);
              setDateTo(to);
            }}
          />
          <AddCityForm onCityAdded={handleCityAdded} />
        </aside>

        <main>
          <FeaturedEvents events={topEvents} />

          <section className="events-section">
            <div className="events-header">
              <h2 className="section-title">
                All Events
                <span className="section-subtitle">{subtitle}</span>
              </h2>
              <span className="events-count">
                {events.length} event{events.length !== 1 ? "s" : ""}
              </span>
            </div>

            <EventGrid events={events} loading={loading} />
          </section>
        </main>
      </div>

      <footer className="footer">
        Discovery Event Platform — Real-time multi-source event aggregation
      </footer>
    </div>
  );
}
