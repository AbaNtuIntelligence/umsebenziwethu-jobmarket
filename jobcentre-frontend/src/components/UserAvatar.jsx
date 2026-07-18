import { useEffect, useState } from "react";
import { mediaUrl } from "../services/api";

function initialsFor(user) {
  const first = user?.first_name?.trim()?.[0] || user?.username?.trim()?.[0] || "U";
  const last = user?.last_name?.trim()?.[0] || "";
  return `${first}${last}`.toUpperCase();
}

export default function UserAvatar({ user, className = "", cacheKey, label }) {
  const [failed, setFailed] = useState(false);
  const src = mediaUrl(user?.avatar, cacheKey);
  const name = label || user?.first_name || user?.username || "User";

  useEffect(() => setFailed(false), [src]);

  if (src && !failed) {
    return (
      <img
        className={className}
        src={src}
        alt={`${name}'s profile picture`}
        onError={() => setFailed(true)}
      />
    );
  }

  return (
    <span className={`${className} avatar-fallback`} role="img" aria-label={`${name}'s profile picture`}>
      {initialsFor(user)}
    </span>
  );
}
