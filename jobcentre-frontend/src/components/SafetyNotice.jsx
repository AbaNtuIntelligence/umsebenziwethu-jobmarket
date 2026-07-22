import { AlertTriangle, CheckCircle2, ShieldCheck } from "lucide-react";
import { Link } from "react-router-dom";

const VARIANTS = {
  compact: { icon: ShieldCheck, title: "Stay safe", body: "Never pay to apply for a job or share passwords, PINs or one-time codes." },
  detailed: { icon: AlertTriangle, title: "Before you apply", body: "Check the employer and opportunity carefully. Keep communication on the platform where possible and report requests for money or sensitive account information." },
  confirmation: { icon: CheckCircle2, title: "Apply with confidence", body: "Confirm that the job details make sense and that you understand what information will be shared with the employer." },
};

export default function SafetyNotice({ variant = "compact", title, children, showLink = true, className = "" }) {
  const content = VARIANTS[variant] || VARIANTS.compact;
  const Icon = content.icon;
  return <aside className={`safety-notice safety-notice-${variant} ${className}`.trim()} aria-label={title || content.title}>
    <Icon className="safety-notice-icon" aria-hidden="true" />
    <div><strong>{title || content.title}</strong><p>{children || content.body}</p>{showLink && <Link to="/safety">Visit the Safety Centre</Link>}</div>
  </aside>;
}
