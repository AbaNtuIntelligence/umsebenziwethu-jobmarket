import { ArrowLeft, Save } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import api, { errorMessage } from "../services/api";
import { useAuth } from "../state/AuthContext";
import { JOB_CATEGORIES, JOB_CATEGORY_VALUES } from "../data/jobCategories";

export default function EditJobPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get(`/jobs/${id}/`)
      .then(({ data }) => setJob(data))
      .catch((requestError) => setError(errorMessage(requestError)))
      .finally(() => setLoading(false));
  }, [id]);

  if (user?.role !== "employer") return <div className="card empty">This page is for employers.</div>;
  if (loading) return <div className="card empty">Loading listing…</div>;
  if (!job) return <div className="alert error">{error || "Listing not found."}</div>;

  async function submit(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    const form = new FormData(event.currentTarget);
    const payload = Object.fromEntries(form);
    payload.urgent = form.has("urgent");
    Object.keys(payload).forEach((key) => { if (payload[key] === "") delete payload[key]; });
    try {
      await api.patch(`/jobs/${id}/`, payload);
      navigate("/employer");
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setSaving(false);
    }
  }

  return <div className="form-card">
    <Link className="back" to="/employer"><ArrowLeft /> Back to my listings</Link>
    <h1>Edit opportunity</h1>
    <p>Saved changes return this listing to pending review. Applications and history remain protected.</p>
    {error && <div className="alert error">{error}</div>}
    <form className="form-grid" onSubmit={submit}>
      <label className="span-2">Job title<input name="title" defaultValue={job.title} required /></label>
      <label>Category<select name="category" defaultValue={job.category} required>{!JOB_CATEGORY_VALUES.includes(job.category) && <option value={job.category}>{job.category} (legacy category)</option>}{JOB_CATEGORIES.map((category) => <option value={category.value} key={category.value}>{category.value}</option>)}</select><small className="field-help">Choose the closest category so this opportunity appears in relevant searches.</small></label>
      <label>Employment type<select name="employment_type" defaultValue={job.employment_type}><option value="permanent">Permanent</option><option value="contract">Contract</option><option value="temporary">Temporary</option><option value="part_time">Part-time</option><option value="internship">Internship</option></select></label>
      <label>Province<input name="province" defaultValue={job.province} required /></label>
      <label>City or town<input name="city" defaultValue={job.city} required /></label>
      <label>Workplace<select name="workplace" defaultValue={job.workplace}><option value="onsite">On-site</option><option value="hybrid">Hybrid</option><option value="remote">Remote</option></select></label>
      <label>Closing date<input type="date" name="closing_date" defaultValue={job.closing_date} required /></label>
      <label>Positions available<input type="number" name="positions_available" min="1" defaultValue={job.positions_available} required /></label>
      <label className="checkbox"><input type="checkbox" name="urgent" defaultChecked={job.urgent} />Urgent opportunity</label>
      <label className="span-2">Description<textarea name="description" rows="6" defaultValue={job.description} required /></label>
      <label className="span-2">Requirements<textarea name="requirements" rows="4" defaultValue={job.requirements} /></label>
      <label>Minimum salary<input type="number" name="salary_min" min="0" defaultValue={job.salary_min || ""} /></label>
      <label>Maximum salary<input type="number" name="salary_max" min="0" defaultValue={job.salary_max || ""} /></label>
      <button className="button primary span-2" disabled={saving}><Save />{saving ? "Saving…" : "Save changes"}</button>
    </form>
  </div>;
}
