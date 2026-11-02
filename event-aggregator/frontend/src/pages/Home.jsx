import { useEffect, useState } from 'react';
import { api } from '../api/client';
import Header from '../components/Header';
import EventCard from '../components/EventCard';
import { useAuth } from '../context/AuthContext';
import { useSchools, shortName } from '../useSchools';
import { Link } from 'react-router-dom';

export default function Home() {
  const [categories, setCategories] = useState([]);
  const [activeCategory, setActiveCategory] = useState('All');
  const [query, setQuery] = useState('');
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { user } = useAuth();
  const schools = useSchools();
  const hasSchool = Boolean(user?.school);
  const [view, setView] = useState('mine');

  useEffect(() => {
    api.listCategories().then((d) => setCategories(d.categories)).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    setError('');
    const params = {};
    if (activeCategory !== 'All') params.category = activeCategory;
    if (query) params.q = query;
    if (hasSchool && view === 'mine') params.for_school = user.school;

    const timeout = setTimeout(() => {
      api.listEvents(params)
        .then((d) => setEvents(d.events))
        .catch((e) => setError(e.message))
        .finally(() => setLoading(false));
    }, 250); // light debounce on keyword search

    return () => clearTimeout(timeout);
  }, [activeCategory, query, view, hasSchool]);

  return (
    <>
      <Header title="KABU Events" subtitle="Discover events at Kabarak University" />
      <div className="content">
        <input
          className="search-bar"
          placeholder="Search by title, venue or organiser…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />

        {hasSchool ? (
          <div className="view-toggle">
            <button className={view === 'mine' ? 'active' : ''} onClick={() => setView('mine')}>For me</button>
            <button className={view === 'all' ? 'active' : ''} onClick={() => setView('all')}>All events</button>
          </div>
        ) : user?.role === 'student' ? (
          <p className="meta" style={{ marginBottom: 12 }}>
            <Link to="/profile" style={{ color: 'var(--blue)', fontWeight: 600 }}>Set your school</Link> to see events for you first.
          </p>
        ) : null}
        {hasSchool && view === 'mine' && (
          <p className="meta" style={{ margin: '-4px 0 12px' }}>
            Open events plus {shortName(schools, user.school)}
          </p>
        )}
        <div className="chip-row">
          <button
            className={`chip${activeCategory === 'All' ? ' active' : ''}`}
            onClick={() => setActiveCategory('All')}
          >
            All
          </button>
          {categories.map((c) => (
            <button
              key={c.id}
              className={`chip${activeCategory === c.name ? ' active' : ''}`}
              onClick={() => setActiveCategory(c.name)}
            >
              {c.name[0].toUpperCase() + c.name.slice(1)}
            </button>
          ))}
        </div>

        <p className="section-title">Upcoming Events</p>

        {error && <div className="error-banner">{error}</div>}
        {loading && <p className="empty-state">Loading events…</p>}
        {!loading && events.length === 0 && (
          <p className="empty-state">No events match your filters yet. Check back soon!</p>
        )}
        <div className="event-grid">
          {events.map((ev) => <EventCard key={ev.id} event={ev} />)}
        </div>
      </div>
    </>
  );
}
