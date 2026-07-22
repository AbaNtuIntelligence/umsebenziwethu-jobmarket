import { ArrowLeft, BriefcaseBusiness, MapPin, Send, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import api, { errorMessage, mediaUrl } from "../services/api";

function rows(data) {
  return data.results || data;
}

export default function TalentProfilePage() {
  const { id } = useParams();
  const [profile, setProfile] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [message, setMessage] = useState("");
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);

  useEffect(() => {
    Promise.all([api.get(`/auth/job-seekers/${id}/`), api.get("/jobs/mine/")])
      .then(([profileResult, jobsResult]) => {
        setProfile(profileResult.data);
        setJobs(rows(jobsResult.data).filter((job) => job.status === "published" && !job.is_expired));
      })
      .catch((requestError) => setMessage(errorMessage(requestError)));
  }, [id]);

  async function invite(event) {
    event.preventDefault();
    setSending(true);
    setMessage("");
    try {
      const form = new FormData(event.currentTarget);
      await api.post("/job-invitations/", {
        candidate_profile: Number(id),
        job: Number(form.get("job")),
        message: form.get("message") || "",
      });
      setSent(true);
      setMessage("Invitation sent. The job seeker has been notified and can open the opportunity directly.");
    } catch (requestError) {
      setMessage(errorMessage(requestError));
    } finally {
      setSending(false);
    }
  }

  if (!profile) return <div className="card empty">{message || "Loading professional profile…"}</div>;
  const initials = profile.name.split(" ").map((part) => part[0]).slice(0, 2).join("").toUpperCase();
  const skills = profile.skills.split(",").map((skill) => skill.trim()).filter(Boolean);

  return <>
    <Link className="back" to="/job-seekers"><ArrowLeft /> Back to job seekers</Link>
    <article className="talent-profile">
      <header>
        {profile.avatar ? <img src={mediaUrl(profile.avatar)} alt={`${profile.name}'s profile`} /> : <span className="talent-profile-fallback">{initials}</span>}
        <div>
          <span className="open-to-work"><ShieldCheck /> Open to work</span>
          <h1>{profile.name}</h1>
          <p>{profile.professional_headline || "Job seeker open to opportunities"}</p>
        </div>
      </header>
      <section className="talent-profile-facts">
        {(profile.city || profile.province) && <span><MapPin />{[profile.city, profile.province].filter(Boolean).join(", ")}</span>}
        {(profile.sector || profile.industry) && <span><BriefcaseBusiness />{[profile.sector, profile.industry].filter(Boolean).join(" · ")}</span>}
        {profile.availability && <span><b>Availability:</b> {profile.availability}</span>}
      </section>
      {profile.bio && <section><h2>Professional introduction</h2><p className="talent-profile-bio">{profile.bio}</p></section>}
      <section><h2>Skills</h2>{skills.length ? <div className="talent-skills">{skills.map((skill) => <span key={skill}>{skill}</span>)}</div> : <p>No skills have been added yet.</p>}</section>
    </article>

    <section className="invite-panel">
      <div><Send /><div><h2>Invite to apply</h2><p>Choose one of your open opportunities. The job seeker receives an official notification; their private details remain protected.</p></div></div>
      {message && <div className={sent ? "alert" : "alert error"}>{message}</div>}
      {jobs.length ? <form onSubmit={invite} className="form-stack">
        <label>Opportunity<select name="job" required defaultValue=""><option value="" disabled>Choose a published job</option>{jobs.map((job) => <option value={job.id} key={job.id}>{job.title} · closes {job.closing_date}</option>)}</select></label>
        <label>Personal message (optional)<textarea name="message" rows="4" maxLength="1000" placeholder="Tell the job seeker why this opportunity may suit their skills." /></label>
        <button className="button primary" disabled={sending || sent}>{sending ? "Sending invitation…" : sent ? "Invitation sent" : "Send invitation"}</button>
      </form> : <div className="empty-soft"><p>You need a published, open job before inviting this candidate.</p><Link className="button primary" to="/post-job">Post a job</Link></div>}
    </section>
  </>;
}
