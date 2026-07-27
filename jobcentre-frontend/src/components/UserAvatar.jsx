import { useEffect, useState } from "react";
import { mediaUrl } from "../services/api";

export default function UserAvatar({
  user,
  className = "",
  cacheKey,
}) {
  const avatar = mediaUrl(user?.avatar, cacheKey);
  const [imageFailed, setImageFailed] = useState(false);

  useEffect(() => {
    setImageFailed(false);
  }, [avatar]);

  const initials = `${user?.first_name?.[0] || user?.username?.[0] || "U"}${
    user?.last_name?.[0] || ""
  }`.toUpperCase();

  if (avatar && !imageFailed) {
    return (
      <img
        className={className}
        src={avatar}
        alt={`${user?.first_name || user?.username || "User"} profile`}
        onError={() => setImageFailed(true)}
      />
    );
  }

  return (
    <span
      className={`${className} avatar-fallback`.trim()}
      aria-label={`${user?.first_name || user?.username || "User"} profile`}
    >
      {initials}
    </span>
  );
}