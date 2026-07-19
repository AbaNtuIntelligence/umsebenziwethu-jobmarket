import { PlusCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import JobCard from "../components/JobCard";
import api from "../services/api";
import { useAuth } from "../state/AuthContext";

export default function EmployerDashboard() {
  const { user } = useAuth();
  const [jobs, setJobs] = useState([]);

  useEffect(() => {
    if (user?.role === "employer") {
      api
        .get("/jobs/mine/")
        .then(({ data }) => setJobs(data.results || data));
    }
  }, [user]);

  if (user?.role !== "employer") {
    return (
      <div className="card empty">
        This page is for employers.
      </div>
    );
  }

  return (
    <>
      <div className="dashboard-heading">
        <div>
          <h1>My opportunities</h1>
          <p>Manage your vacancies and incoming applicants.</p>
        </div>

        <Link className="button primary" to="/post-job">
          <PlusCircle />
          Post a job
        </Link>
      </div>

      {jobs.length ? (
        jobs.map((job) => (
          <div key={job.id}>
            <span className={`status ${job.status}`}>
              {job.status.replace("_", " ")}
            </span>

            {job.status === "pending" && (
              <p className="moderation-note">
                Our administrator is reviewing this job before it becomes
                public.
              </p>
            )}

            {job.status === "rejected" && (
              <div className="alert error">
                <b>Changes required:</b>{" "}
                {job.rejection_reason ||
                  "Contact the administrator for details."}
              </div>
            )}

            <JobCard job={job} />
          </div>
        ))
      ) : (
        <div className="card empty">
          <h2>No vacancies yet</h2>
          <Link to="/post-job">Post your first opportunity</Link>
        </div>
      )}
    </>
  );
}