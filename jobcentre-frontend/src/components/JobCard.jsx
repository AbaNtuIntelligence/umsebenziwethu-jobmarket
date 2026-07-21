import {
  Bookmark,
  Briefcase,
  Building2,
  Clock3,
  MapPin,
  Share2,
  UsersRound,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api, { mediaUrl } from "../services/api";
import { useAuth } from "../state/AuthContext";



function daysLeft(date) { return Math.ceil((new Date(`${date}T23:59:59`) - new Date()) / 86400000); }
export default function JobCard({job}) {
  const {user} = useAuth(); const navigate = useNavigate(); const left = daysLeft(job.closing_date);
  const image = job.media?.find(item => item.media_type === "image");
  const avatar = mediaUrl(job.employer_avatar);
  const [avatarFailed, setAvatarFailed] = useState(false);

useEffect(() => {
  setAvatarFailed(false);
}, [avatar]);

  async function save() { if (!user) return navigate("/login"); await api.post("/saved-jobs/", {job: job.id}); }
  async function share() { const url = `${location.origin}/jobs/${job.id}`; if (navigator.share) await navigator.share({title: job.title, url}); else await navigator.clipboard.writeText(url); }
  return <article className="job-card">
    <header className="job-author"><div className="company-logo">
  {avatar && !avatarFailed ? (
    <img
      src={avatar}
      alt={`${job.organisation_name || "Employer"} profile picture`}
      loading="lazy"
      onError={() => setAvatarFailed(true)}
    />
  ) : (
    <Building2 />
  )}
</div><div><b>{job.organisation_name}</b>{job.employer_verified && <span className="verified">✓ Verified</span>}<small>Posted {new Date(job.created_at).toLocaleDateString("en-ZA")}</small></div>{job.urgent && <span className="urgent">Urgent</span>}</header>
    {image && <img className="job-cover" src={image.file} alt="" loading="lazy"/>}
    <div className="job-body"><Link to={`/jobs/${job.id}`}><h2>{job.title}</h2></Link><p className="clamp">{job.description}</p><div className="facts"><span><MapPin/>{job.city}, {job.province}</span><span><Briefcase/>{job.employment_type.replace("_", "-")}</span><span><UsersRound/>{job.positions_available} position{job.positions_available !== 1 && "s"}</span><span className={left <= 2 ? "deadline" : ""}><Clock3/>Closes in {left} day{left !== 1 && "s"}</span></div></div>
    <footer className="job-actions"><button onClick={save}><Bookmark/>Save</button><button onClick={share}><Share2/>Share</button><Link className="apply-button" to={`/jobs/${job.id}`}>View job</Link></footer>
  </article>;
}
