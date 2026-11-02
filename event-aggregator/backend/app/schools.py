"""Schools of Kabarak University (main campus). Students record their school,
and organisers can mark an event as meant for particular schools. The feed's
"For me" view shows events open to everyone plus those for the student's own
school; the "All events" view still shows everything."""
SCHOOLS = {
    "business": "School of Business and Economics",
    "education": "School of Education, Humanities and Social Sciences",
    "law": "School of Law",
    "medicine": "School of Medicine and Health Sciences",
    "music": "School of Music and Media",
    "pharmacy": "School of Pharmacy",
    "sset": "School of Science, Engineering and Technology",
}
ALL = "all"


def parse_audience(value):
    """Accept 'all', None, or a list of school codes; return the stored string
    ('all' or comma-separated codes) or raise ValueError."""
    if value in (None, "", ALL) or value == [ALL]:
        return ALL
    if isinstance(value, str):
        value = [v.strip() for v in value.split(",") if v.strip()]
    if not isinstance(value, list) or not value:
        raise ValueError("audience must be 'all' or a list of school codes")
    codes = sorted({str(v).strip().lower() for v in value})
    if any(c not in SCHOOLS for c in codes):
        raise ValueError("Unknown school in audience")
    return ",".join(codes)


def audience_list(stored):
    return [] if not stored or stored == ALL else stored.split(",")
