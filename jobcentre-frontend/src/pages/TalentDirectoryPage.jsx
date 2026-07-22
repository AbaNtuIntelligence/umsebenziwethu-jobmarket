import { BriefcaseBusiness, MapPin, Search, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { errorMessage, mediaUrl } from "../services/api";

function rows(data) {
  return data.results || data;
}

function TalentCard({ candidate }) {
  const initials = candidate.name
    .split(" ")
    .map((part) => part[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
  const skills = candidate.skills
    .split(",")
    .map((skill) => skill.trim())
    .filter(Boolean);

  return <article className="talent-card">
    <header className="talent-author">
      <Link to={`/job-seekers/${candidate.id}`} className="talent-avatar-link">
        {candidate.avatar
          ? <img src={mediaUrl(candidate.avatar)} alt={`${candidate.name}'s profile`} />
          : <span className="talent-avatar-fallback">{initials}</span>}
      </Link>
      <div>
        <h2><Link to={`/job-seekers/${candidate.id}`}>{candidate.name}</Link></h2>
        <p>{candidate.professional_headline || "Job seeker open to opportunities"}</p>
      </div>
      <span className="open-to-work"><ShieldCheck /> Open to work</span>
    </header>

    <div className="talent-body">
      {(candidate.city || candidate.province) && <p className="talent-location"><MapPin />{[candidate.city, candidate.province].filter(Boolean).join(", ")}</p>}
      {(candidate.sector || candidate.industry) && <p className="talent-sector"><BriefcaseBusiness />{[candidate.sector, candidate.industry].filter(Boolean).join(" · ")}</p>}
      {candidate.bio && <p className="talent-bio">{candidate.bio}</p>}
      {skills.length > 0 && <div className="talent-skills">{skills.map((skill) => <span key={skill}>{skill}</span>)}</div>}
      <footer className="talent-card-footer">
        {candidate.availability ? <span><b>Availability</b> {candidate.availability}</span> : <span />}
        <Link className="button primary" to={`/job-seekers/${candidate.id}`}>View seeker profile</Link>
      </footer>
    </div>
  </article>;
}

export default function TalentDirectoryPage() {
  const [candidates, setCandidates] = useState([]);
  const [filters, setFilters] = useState({ search: "", sector: "", province: "" });
  const [query, setQuery] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    setError("");
    api.get("/auth/job-seekers/", { params: query })
      .then(({ data }) => setCandidates(rows(data)))
      .catch((requestError) => setError(errorMessage(requestError)))
      .finally(() => setLoading(false));
  }, [query]);

  function change(event) {
    setFilters((current) => ({ ...current, [event.target.name]: event.target.value }));
  }

  function search(event) {
    event.preventDefault();
    setQuery(Object.fromEntries(Object.entries(filters).filter(([, value]) => value.trim())));
  }

  function clear() {
    setFilters({ search: "", sector: "", province: "" });
    setQuery({});
  }

  return <>
    <section className="talent-intro">
      <small>Employer talent marketplace</small>
      <h1>Discover job seekers</h1>
      <p>Browse professional profiles shared by people who are open to work. Private contact details and résumés are not displayed.</p>
      <form className="talent-search" onSubmit={search}>
        <label className="talent-keyword"><Search /><input name="search" value={filters.search} onChange={change} placeholder="Search skills, headline or city" /></label>
        <input name="sector" value={filters.sector} onChange={change} placeholder="Sector" />
        <input name="province" value={filters.province} onChange={change} placeholder="Province" />
        <button className="button primary">Find talent</button>
        {Object.keys(query).length > 0 && <button type="button" className="button ghost" onClick={clear}>Clear</button>}
      </form>
    </section>

    {loading
      ? <div className="card empty">Loading professional profiles…</div>
      : error
        ? <div className="alert error">{error}</div>
        : candidates.length
          ? candidates.map((candidate) => <TalentCard candidate={candidate} key={candidate.id} />)
          : <div className="card empty"><h2>No matching job seekers</h2><p>Try a broader skill, sector or province.</p></div>}
  </>;
}
