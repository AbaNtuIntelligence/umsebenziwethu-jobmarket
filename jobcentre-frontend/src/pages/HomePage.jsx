import { Search, SlidersHorizontal } from "lucide-react";
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import JobCard from "../components/JobCard";
import api, {errorMessage} from "../services/api";

export default function HomePage() {
  const [params, setParams] = useSearchParams(); const [jobs, setJobs] = useState([]); const [loading, setLoading] = useState(true); const [error, setError] = useState("");
  const search = params.get("search") || "";
  useEffect(() => { setLoading(true); api.get("/jobs/", {params: Object.fromEntries(params)}).then(({data}) => setJobs(data.results || data)).catch(e => setError(errorMessage(e))).finally(() => setLoading(false)); }, [params.toString()]);
  function submit(e) { e.preventDefault(); const value = new FormData(e.currentTarget).get("search"); setParams(value ? {search: value} : {}); }
  return <><section className="feed-intro"><h1>Opportunities near you</h1><p>Fresh, trusted job openings in one place.</p><form className="search-bar" onSubmit={submit}><Search/><input key={search} name="search" defaultValue={search} placeholder="Job title, skill or company"/><button>Search</button></form><div className="chips">{["Urgent", "Driving", "Retail", "No experience"].map(x=><button key={x} onClick={() => setParams(x === "Urgent" ? {urgent:"true"} : {search:x})}>{x}</button>)}<button><SlidersHorizontal/>Filters</button></div></section>{loading ? <div className="card empty">Loading opportunities…</div> : error ? <div className="alert error">{error}</div> : jobs.length ? jobs.map(job=><JobCard job={job} key={job.id}/>) : <div className="card empty"><h2>No jobs found</h2><p>Try another keyword or clear your filters.</p></div>}</>;
}
