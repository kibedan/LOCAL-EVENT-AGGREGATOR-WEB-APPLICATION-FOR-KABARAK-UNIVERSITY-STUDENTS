import { useState } from 'react';
import { api } from '../api/client';
import Header from '../components/Header';
import EventCard from '../components/EventCard';

export default function Search() {
  const [query, setQuery] = useState('');
  const [location, setLocation] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [results, setResults] = useState([]);
  const [searched, setSearched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSearch(e) {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSearched(true);
    try {
      const d = await api.listEvents({ q: query, location, date_from: dateFrom, date_to: dateTo });
      setResults(d.events);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <Header title="Search Events" subtitle="Find events by keyword, venue or club" />
      <div className="content">
        <form onSubmit={handleSearch}>
          <input
            className="search-bar"
            placeholder='Try "free food", a club name, or a topic…'
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <input
            className="search-bar"
            placeholder="Venue (optional)"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
          />
          <div className="date-row">
            <div className="form-group">
              <label htmlFor="date-from">From</label>
              <input id="date-from" type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
            </div>
            <div className="form-group">
              <label htmlFor="date-to">To</label>
              <input id="date-to" type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
            </div>
          </div>
          <button className="btn btn-primary" style={{ marginBottom: 16 }} disabled={loading}>
            {loading ? 'Searching…' : 'Search'}
          </button>
        </form>

        {error && <div className="error-banner">{error}</div>}
        {searched && !loading && results.length === 0 && (
          <p className="empty-state">No events match that search.</p>
        )}
        <div className="event-grid">
          {results.map((ev) => <EventCard key={ev.id} event={ev} />)}
        </div>
      </div>
    </>
  );
}
