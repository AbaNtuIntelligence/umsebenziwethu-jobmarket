import { Search } from "lucide-react";
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import JobCard from "../components/JobCard";
import { JOB_CATEGORIES } from "../data/jobCategories";
import api, { errorMessage } from "../services/api";

export default function HomePage() {
  const [params, setParams] = useSearchParams();
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const search = params.get("search") || "";

  useEffect(() => {
    setLoading(true);
    setError("");
    api.get("/jobs/", { params: Object.fromEntries(params) })
      .then(({ data }) => setJobs(data.results || data))
      .catch((requestError) => setError(errorMessage(requestError)))
      .finally(() => setLoading(false));
  }, [params.toString()]);

  function submit(event) {
    event.preventDefault();
    const value = new FormData(event.currentTarget).get("search").trim();
    setParams(value ? { search: value } : {});
  }

  function chooseCategory(event) {
    const query = event.target.value;
    setParams(query ? { search: query } : {});
  }

  return <>
    <section className="feed-intro">
      <h1>Opportunities near you</h1>
      <p>Fresh, trusted job openings in one place.</p>
      <form className="search-bar" onSubmit={submit}>
        <Search />
        <input key={search} name="search" defaultValue={search} placeholder="Job title, skill or company" />
        <button>Search</button>
      </form>

      <div className="marketplace-tagline">
        <strong>Your skills have value.</strong>
        <span>Your next opportunity starts with UmsebenziWethu.</span>
      </div>

      <label className="mobile-category-browser">
        Browse job categories
        <select value={JOB_CATEGORIES.find((category) => category.query === search)?.query || ""} onChange={chooseCategory}>
          <option value="">All opportunities</option>
          {JOB_CATEGORIES.map((category) => <option value={category.query} key={category.value}>{category.value}</option>)}
        </select>
      </label>
    </section>

    {loading
      ? <div className="card empty">Loading opportunities…</div>
      : error
        ? <div className="alert error">{error}</div>
        : jobs.length
          ? jobs.map((job) => <JobCard job={job} key={job.id} />)
          : <div className="card empty"><h2>No jobs found</h2><p>Try another keyword or clear your filters.</p></div>}
  </>;
}
