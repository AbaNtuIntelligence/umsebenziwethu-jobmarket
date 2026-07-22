import { Archive, Pencil, PlusCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import JobCard from "../components/JobCard";
import api, { errorMessage } from "../services/api";
import { useAuth } from "../state/AuthContext";

export default function EmployerDashboard() {
  const { user } = useAuth();
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [closingId, setClosingId] = useState(null);

  useEffect(() => {
    if (user?.role !== "employer") {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError("");
    api.get("/jobs/mine/")
      .then(({ data }) => setJobs(data.results || data))
      .catch((requestError) => setError(errorMessage(requestError)))
      .finally(() => setLoading(false));
  }, [user]);

  async function closeJob(job) {
    const confirmed = window.confirm(
      `Close “${job.title}”? The vacancy will leave the public feed, but its applications and history will be preserved.`
    );
    if (!confirmed) return;

    setClosingId(job.id);
    setError("");
    try {
      const { data } = await api.post(`/jobs/${job.id}/close/`);
      setJobs((current) => current.map((item) => item.id === job.id ? data : item));
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setClosingId(null);
    }
  }

  if (user?.role !== "employer") {
    return <div className="card empty">This page is available only to employer accounts.</div>;
  }

  return (
    <>
      <div className="dashboard-heading">
        <div>
          <h1>My opportunities</h1>
          <p>Create, edit and close your job opportunities.</p>
        </div>
        <Link className="button primary" to="/post-job">
          <PlusCircle /> Post a job
        </Link>
      </div>

      {error && <div className="alert error" role="alert">{error}</div>}

      {loading ? (
        <div className="card empty">Loading your vacancies…</div>
      ) : jobs.length ? (
        jobs.map((job) => (
          <section className="employer-listing" key={job.id}>
            <span className={`status ${job.status}`}>{job.status.replaceAll("_", " ")}</span>

            {job.status === "pending" && (
              <p className="moderation-note">Our administrator is reviewing this job before it becomes public.</p>
            )}

            {job.status === "rejected" && (
              <div className="alert error">
                <b>Changes required:</b>{" "}
                {job.rejection_reason || "Contact the administrator for details."}
              </div>
            )}

            {job.status === "closed" && (
              <div className="alert">This listing is closed. Its applications and history remain preserved.</div>
            )}

            <JobCard job={job} />

            <div className="listing-management">
              <Link className="button ghost" to={`/jobs/${job.id}/edit`}>
                <Pencil /> Edit &amp; manage media
              </Link>
              {job.status !== "closed" && (
                <button
                  type="button"
                  className="button danger"
                  disabled={closingId === job.id}
                  onClick={() => closeJob(job)}
                >
                  <Archive /> {closingId === job.id ? "Closing…" : "Close listing"}
                </button>
              )}
            </div>
          </section>
        ))
      ) : (
        <div className="card empty">
          <h2>No vacancies yet</h2>
          <p>Create your first opportunity and submit it for review.</p>
          <Link className="button primary" to="/post-job">
            <PlusCircle /> Post your first opportunity
          </Link>
        </div>
      )}
    </>
  );
}
