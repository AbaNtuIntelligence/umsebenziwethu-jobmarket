import {
  FileText,
  Image,
  Upload,
  Video,
} from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api, { errorMessage } from "../services/api";
import { useAuth } from "../state/AuthContext";
import { JOB_CATEGORIES } from "../data/jobCategories";

const UPLOAD_BATCH_SIZE = 3;

export default function PostJobPage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [files, setFiles] = useState([]);
  const [failedFiles, setFailedFiles] = useState([]);
  const [createdJob, setCreatedJob] = useState(null);
  const [submissionStage, setSubmissionStage] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  if (user?.role !== "employer") {
    return (
      <div className="card empty">
        Only employer accounts can post jobs.
      </div>
    );
  }

  async function uploadMedia(jobId, selectedFiles) {
    if (!selectedFiles.length) {
      return true;
    }

    const failed = [];
    let completed = 0;

    setSubmissionStage(
      `Uploading 0 of ${selectedFiles.length} attachments…`
    );

    for (
      let index = 0;
      index < selectedFiles.length;
      index += UPLOAD_BATCH_SIZE
    ) {
      const batch = selectedFiles.slice(
        index,
        index + UPLOAD_BATCH_SIZE
      );

      const results = await Promise.allSettled(
        batch.map((file) => {
          const media = new FormData();
          media.append("file", file);

          // Axios sets the correct multipart boundary automatically.
          return api.post(`/jobs/${jobId}/media/`, media);
        })
      );

      results.forEach((result, resultIndex) => {
        if (result.status === "rejected") {
          failed.push(batch[resultIndex]);
        }
      });

      completed += batch.length;

      setSubmissionStage(
        `Uploaded ${completed} of ${selectedFiles.length} attachments…`
      );
    }

    setFailedFiles(failed);

    if (failed.length) {
      setError(
        `The job was saved, but ${failed.length} attachment${
          failed.length === 1 ? "" : "s"
        } could not be uploaded. Retry the failed upload without submitting the job again.`
      );

      setSubmissionStage("Job saved with incomplete attachments.");
      return false;
    }

    return true;
  }

  async function submit(event) {
    event.preventDefault();

    // Prevent accidental duplicate jobs after a partial upload.
    if (createdJob) {
      return;
    }

    setSaving(true);
    setError("");
    setFailedFiles([]);
    setSubmissionStage("Creating your job post…");

    try {
      const payload = Object.fromEntries(
        new FormData(event.currentTarget)
      );

      Object.keys(payload).forEach((key) => {
        if (payload[key] === "") {
          delete payload[key];
        }
      });

      const { data: job } = await api.post("/jobs/", payload);

      setCreatedJob(job);

      const mediaSaved = await uploadMedia(job.id, files);

      if (!mediaSaved) {
        return;
      }

      setSubmissionStage("Job submitted for review.");
      navigate("/employer");
    } catch (requestError) {
      setError(errorMessage(requestError));
      setSubmissionStage("");
    } finally {
      setSaving(false);
    }
  }

  async function retryFailedUploads() {
    if (!createdJob || !failedFiles.length) {
      return;
    }

    setSaving(true);
    setError("");

    try {
      const mediaSaved = await uploadMedia(
        createdJob.id,
        failedFiles
      );

      if (mediaSaved) {
        setSubmissionStage("All attachments uploaded successfully.");
        navigate("/employer");
      }
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setSaving(false);
    }
  }

  function handleFiles(event) {
    const selectedFiles = Array.from(event.target.files || []);

    setFiles(selectedFiles);
    setFailedFiles([]);
    setError("");
  }

  return (
    <div className="form-card">
      <h1>Post an opportunity</h1>
      <p>Keep it clear, honest and easy to understand.</p>

      {error && (
        <div className="alert error" role="alert">
          {error}
        </div>
      )}

      {submissionStage && (
        <div className="submission-progress" role="status">
          {saving && <span className="submission-spinner" />}
          <span>{submissionStage}</span>
        </div>
      )}

      <form className="form-grid" onSubmit={submit}>
        <label className="span-2">
          Job title
          <input
            name="title"
            required
            placeholder="e.g. Delivery Driver"
          />
        </label>

        <label>
          Category
          <select name="category" required defaultValue="">
            <option value="" disabled>Select the best-matching category</option>
            {JOB_CATEGORIES.map((category) => <option value={category.value} key={category.value}>{category.value}</option>)}
          </select>
          <small className="field-help">This determines where job seekers discover the opportunity.</small>
        </label>

        <label>
          Employment type
          <select name="employment_type">
            <option value="permanent">Permanent</option>
            <option value="contract">Contract</option>
            <option value="temporary">Temporary</option>
            <option value="part_time">Part-time</option>
            <option value="internship">Internship</option>
          </select>
        </label>

        <label>
          Province
          <input name="province" required />
        </label>

        <label>
          City or town
          <input name="city" required />
        </label>

        <label>
          Workplace
          <select name="workplace">
            <option value="onsite">On-site</option>
            <option value="hybrid">Hybrid</option>
            <option value="remote">Remote</option>
          </select>
        </label>

        <label>
          Closing date
          <input
            type="date"
            name="closing_date"
            required
          />
        </label>

        <label>
          Positions available
          <input
            type="number"
            name="positions_available"
            min="1"
            defaultValue="1"
          />
        </label>

        <label className="checkbox">
          <input
            type="checkbox"
            name="urgent"
            value="true"
          />
          Urgent opportunity
        </label>

        <label className="span-2">
          Description
          <textarea
            name="description"
            rows="6"
            required
          />
        </label>

        <label className="span-2">
          Requirements
          <textarea
            name="requirements"
            rows="4"
          />
        </label>

        <label>
          Minimum salary
          <input
            type="number"
            name="salary_min"
            min="0"
          />
        </label>

        <label>
          Maximum salary
          <input
            type="number"
            name="salary_max"
            min="0"
          />
        </label>

        <div className="upload-box span-2">
          <Upload />
          <b>Add supporting media</b>

          <p>
            Images up to 8 MB, videos up to 50 MB and PDFs up to
            10 MB.
          </p>

          <div className="media-types">
            <span>
              <Image />
              JPG, PNG, WebP
            </span>

            <span>
              <Video />
              MP4, WebM
            </span>

            <span>
              <FileText />
              PDF
            </span>
          </div>

          <input
            type="file"
            multiple
            accept={[
              "image/jpeg",
              "image/png",
              "image/webp",
              "video/mp4",
              "video/webm",
              "application/pdf",
            ].join(",")}
            onChange={handleFiles}
            disabled={saving || Boolean(createdJob)}
          />

          {files.map((file) => (
            <small key={`${file.name}-${file.lastModified}`}>
              {file.name}
            </small>
          ))}
        </div>

        <button
          className="button primary span-2"
          disabled={saving || Boolean(createdJob)}
        >
          {saving
            ? submissionStage || "Submitting…"
            : createdJob
              ? "Job saved"
              : "Submit for review"}
        </button>

        {createdJob && failedFiles.length > 0 && (
          <button
            type="button"
            className="button ghost span-2"
            disabled={saving}
            onClick={retryFailedUploads}
          >
            <Upload />
            Retry {failedFiles.length} failed attachment
            {failedFiles.length === 1 ? "" : "s"}
          </button>
        )}
      </form>
    </div>
  );
}
