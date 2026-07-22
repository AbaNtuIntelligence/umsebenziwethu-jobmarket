import { AlertTriangle, BadgeCheck, Ban, Flag, KeyRound, ShieldCheck, UserCheck } from "lucide-react";
import { Link } from "react-router-dom";
import SafetyNotice from "../components/SafetyNotice";

const warningSigns = [
  "You are asked to pay an application, training, equipment or placement fee.",
  "Someone asks for your password, banking PIN, card details or one-time code.",
  "The offer promises unrealistic pay, avoids clear job details or pressures you to act immediately.",
  "The employer asks for unnecessary identity documents before a genuine recruitment step.",
  "Communication suddenly moves to an unrelated account or person.",
];

export default function SafetyCentrePage() {
  return <div className="safety-centre">
    <header className="safety-hero"><ShieldCheck aria-hidden="true" /><div><span>Open opportunity · visible reputation · shared responsibility</span><h1>UmsebenziWethu Safety Centre</h1><p>Practical guidance for safer job searching, recruiting and professional connections across the Job Market.</p></div></header>
    <SafetyNotice variant="detailed" showLink={false} title="Our safety commitment">UmsebenziWethu connects people and opportunities, but no social platform can guarantee every user, employer or job offer. We provide reporting tools, visible trust signals and safer workflows so the community can make informed decisions.</SafetyNotice>
    <section className="safety-grid" aria-label="Safety guidance">
      <article><Ban /><h2>Never pay to apply</h2><p>A genuine vacancy should not require payment merely to submit an application.</p></article>
      <article><KeyRound /><h2>Protect private information</h2><p>Never share passwords, PINs or one-time codes. Share identity documents only when necessary and with a verified recipient.</p></article>
      <article><UserCheck /><h2>Check who you are dealing with</h2><p>Review the profile, organisation name, contact details and job description. Ask questions when anything is unclear.</p></article>
      <article><Flag /><h2>Report suspicious activity</h2><p>Use “Report this job” on a listing, or contact us through Feedback. Do not continue an unsafe conversation.</p></article>
    </section>
    <section className="safety-section warning-signs"><div className="safety-section-heading"><AlertTriangle /><div><span>Pause and check</span><h2>Common warning signs</h2></div></div><ul>{warningSigns.map((sign) => <li key={sign}>{sign}</li>)}</ul></section>
    <section className="safety-section trust-explainer"><div className="safety-section-heading"><BadgeCheck /><div><span>Understand the labels</span><h2>What verification means</h2></div></div><p>A verification label describes a specific check completed by the platform; it is not a guarantee of conduct, employment or payment. Always assess the opportunity yourself and report new concerns.</p></section>
    <section className="safety-actions"><div><h2>Something does not feel right?</h2><p>Stop, keep any evidence, and tell us what happened.</p></div><Link className="button primary" to="/feedback">Contact support</Link><Link className="button ghost" to="/">Browse opportunities</Link></section>
  </div>;
}
