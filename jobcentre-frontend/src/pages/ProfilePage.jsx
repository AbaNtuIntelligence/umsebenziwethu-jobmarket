import { Camera, FileText } from "lucide-react";
import { useEffect, useState } from "react";
import api, { errorMessage, mediaUrl } from "../services/api";
import { useAuth } from "../state/AuthContext";

export default function ProfilePage() {
  const { user, updateUser } = useAuth();
  const [profile, setProfile] = useState(null);
  const [message, setMessage] = useState("");
  const [preview, setPreview] = useState(mediaUrl(user.avatar));
  const [resumeName, setResumeName] = useState("");

  useEffect(() => {
    api.get("/auth/profile/")
      .then(({ data }) => setProfile(data))
      .catch((requestError) => setMessage(errorMessage(requestError)));
  }, []);

  async function submit(event) {
    event.preventDefault();
    setMessage("");
    try {
      const raw = new FormData(event.currentTarget);
      const avatar = raw.get("avatar");
      const avatarChanged = Boolean(avatar?.size);

      const userForm = new FormData();
      ["first_name", "last_name", "phone"].forEach((key) => userForm.append(key, raw.get(key) || ""));
      if (avatarChanged) userForm.append("avatar", avatar);

      const profileForm = new FormData();
      const profileFields = user.role === "employer"
        ? ["organisation_name", "registration_number", "website", "description"]
        : ["professional_headline", "sector", "industry", "province", "city", "skills", "availability", "bio"];
      profileFields.forEach((key) => profileForm.append(key, raw.get(key) || ""));
      if (user.role === "job_seeker") profileForm.append("directory_visible", raw.has("directory_visible") ? "true" : "false");
      const resume = raw.get("resume");
      if (user.role === "job_seeker" && resume?.size) profileForm.append("resume", resume);

      const profileResult = await api.patch("/auth/profile/", profileForm);
      const userResult = await api.patch("/auth/me/", userForm);
      setProfile(profileResult.data);
      updateUser(userResult.data, { avatarChanged });
      setPreview(mediaUrl(userResult.data.avatar, avatarChanged ? Date.now() : null));
      setResumeName("");
      setMessage("Profile updated successfully.");
    } catch (requestError) {
      setMessage(errorMessage(requestError));
    }
  }

  function chooseAvatar(event) {
    const file = event.target.files?.[0];
    if (file) setPreview(URL.createObjectURL(file));
  }

  if (!profile) return <div className="card empty">{message || "Loading profile…"}</div>;
  const employer = user.role === "employer";
  const initials = `${user.first_name?.[0] || user.username?.[0] || "U"}${user.last_name?.[0] || ""}`.toUpperCase();

  return <div className="form-card">
    <div className="profile-heading">
      <div>
        <h1>{employer ? "Organisation profile" : "Professional profile"}</h1>
        <p>{employer ? "Keep your organisation details recognisable and trustworthy." : "Your profile works like a professional opportunity card for employers."}</p>
      </div>
      {employer && <span className={`verification ${profile.is_verified ? "verified-profile" : ""}`}>{profile.is_verified ? "✓ Verified employer" : "Verification pending"}</span>}
    </div>
    {message && <div className={message.includes("successfully") ? "alert" : "alert error"}>{message}</div>}
    <form className="form-grid" onSubmit={submit}>
      <div className="avatar-editor span-2">
        {preview ? <img src={preview} alt="Profile preview" /> : <span>{initials}</span>}
        <label><Camera />Choose {employer ? "organisation image" : "profile picture"}<input name="avatar" type="file" accept="image/jpeg,image/png,image/webp" onChange={chooseAvatar} /></label>
        <small>Optional JPG, PNG or WebP. Maximum 3 MB.</small>
      </div>
      <label>First name<input name="first_name" defaultValue={user.first_name} /></label>
      <label>Last name<input name="last_name" defaultValue={user.last_name} /></label>
      <label>Phone<input name="phone" defaultValue={user.phone} /></label>

      {employer ? <>
        <label className="span-2">Organisation name<input name="organisation_name" defaultValue={profile.organisation_name} required /></label>
        <label>Registration number<input name="registration_number" defaultValue={profile.registration_number} /></label>
        <label>Website<input name="website" type="url" defaultValue={profile.website} /></label>
        <label className="span-2">About the organisation<textarea name="description" rows="5" defaultValue={profile.description} /></label>
      </> : <>
        <label className="span-2">Professional headline<input name="professional_headline" defaultValue={profile.professional_headline} placeholder="Junior IT Support Technician" /></label>
        <label>Sector<input name="sector" defaultValue={profile.sector} placeholder="Technology" /></label>
        <label>Industry<input name="industry" defaultValue={profile.industry} placeholder="IT support services" /></label>
        <label>Province<input name="province" defaultValue={profile.province} /></label>
        <label>City or town<input name="city" defaultValue={profile.city} /></label>
        <label className="span-2">Skills<input name="skills" defaultValue={profile.skills} placeholder="Technical support, driving, customer service" /></label>
        <label>Availability<input name="availability" defaultValue={profile.availability} placeholder="Immediately available" /></label>
        <label className="span-2">Professional introduction<textarea name="bio" rows="5" defaultValue={profile.bio} /></label>
        <label className="consent span-2"><input type="checkbox" name="directory_visible" defaultChecked={profile.directory_visible} /><span>Make my professional profile discoverable to signed-in employers. Contact details and my résumé stay private.</span></label>
        {profile.resume && <a className="resume-current span-2" href={mediaUrl(profile.resume)} target="_blank" rel="noreferrer"><FileText /> View current résumé</a>}
        <label className="resume-upload span-2">
          <FileText />
          <span><b>{profile.resume ? "Replace résumé or CV" : "Upload résumé or CV"}</b><small>{resumeName || "PDF only, maximum 5 MB"}</small></span>
          <input type="file" name="resume" accept="application/pdf,.pdf" onChange={(event) => setResumeName(event.target.files?.[0]?.name || "")} />
        </label>
      </>}
      <button className="button primary span-2">Save profile</button>
    </form>
  </div>;
}
