import { useState } from "react";
import api, { errorMessage } from "../services/api";

export default function FeedbackPage() {
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submit(event) {
    event.preventDefault();

    if (submitting) return;

    // Preserve the form reference before the asynchronous request.
    const form = event.currentTarget;
    const payload = Object.fromEntries(new FormData(form));

    setSubmitting(true);
    setMessage("");
    setMessageType("");

    try {
      await api.post("/feedback/", payload);

      form.reset();
      setMessage("Thank you—your feedback has been recorded.");
      setMessageType("success");
    } catch (error) {
      setMessage(errorMessage(error));
      setMessageType("error");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="form-card">
      <h1>Help us improve Job Centre</h1>

      <p>
        Tell us what worked and where you became uncertain.
      </p>

      {message && (
        <div
          className={`alert ${messageType}`}
          role={messageType === "error" ? "alert" : "status"}
        >
          {message}
        </div>
      )}

      <form className="form-stack" onSubmit={submit}>
        <label>
          Which area were you using?

          <select name="area" required defaultValue="registration">
            <option value="registration">Registration</option>
            <option value="job_search">Job search</option>
            <option value="job_posting">Job posting</option>
            <option value="application">Application</option>
            <option value="other">Other</option>
          </select>
        </label>

        <label>
          How easy was it?

          <select name="rating" required defaultValue="5">
            <option value="5">5 — Very easy</option>
            <option value="4">4 — Easy</option>
            <option value="3">3 — Acceptable</option>
            <option value="2">2 — Difficult</option>
            <option value="1">1 — Could not complete</option>
          </select>
        </label>

        <label>
          What happened?

          <textarea
            name="message"
            rows="6"
            required
            placeholder="What were you trying to do, and where did you struggle?"
          />
        </label>

        <button
          className="button primary"
          type="submit"
          disabled={submitting}
        >
          {submitting ? "Sending…" : "Send feedback"}
        </button>
      </form>
    </div>
  );
}