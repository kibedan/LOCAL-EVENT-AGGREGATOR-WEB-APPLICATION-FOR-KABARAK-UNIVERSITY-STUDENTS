import { useEffect, useState } from 'react';
import { api } from './api/client';

let cache = null;

/** Schools list from the API, fetched once per page load. */
export function useSchools() {
  const [schools, setSchools] = useState(cache || []);
  useEffect(() => {
    if (cache) return;
    api.schools().then((d) => { cache = d.schools; setSchools(d.schools); }).catch(() => {});
  }, []);
  return schools;
}

/** "School of Medicine and Health Sciences" -> "Medicine and Health Sciences" */
export function shortName(schools, code) {
  const s = schools.find((x) => x.code === code);
  return s ? s.name.replace(/^School of /, '') : code;
}

export function audienceLabel(schools, audience) {
  if (!audience || audience.length === 0) return 'All students';
  return audience.map((c) => shortName(schools, c)).join(', ');
}
