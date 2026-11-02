import { Link } from 'react-router-dom';
import { useSchools, audienceLabel } from '../useSchools';

function formatDate(iso) {
  if (!iso) return '';
  const d = new Date(iso + 'T00:00:00');
  return d.toLocaleDateString(undefined, { weekday: 'short', day: 'numeric', month: 'short' });
}

export default function EventCard({ event }) {
  const catClass = `cat-${(event.category || '').toLowerCase()}`;
  const schools = useSchools();
  return (
    <Link to={`/events/${event.id}`} className={`event-card ${catClass}`}>
      <div className="banner">{event.category}</div>
      <div className="body">
        <p className="title">{event.title}</p>
        <p className="meta">📅 {formatDate(event.date)}{event.time ? ` · ${event.time}` : ''}</p>
        {event.location ? <p className="meta">📍 {event.location}</p> : null}
        {event.audience?.length ? <p className="meta audience">🎓 For {audienceLabel(schools, event.audience)}</p> : null}
        {event.description ? (
          <p className="desc">
            {event.description.length > 90
              ? event.description.slice(0, 90) + '…'
              : event.description}
          </p>
        ) : null}
      </div>
    </Link>
  );
}
