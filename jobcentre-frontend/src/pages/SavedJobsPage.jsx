import { useEffect, useState } from "react";
import JobCard from "../components/JobCard";
import api from "../services/api";
export default function SavedJobsPage(){const [items,setItems]=useState([]);useEffect(()=>{api.get("/saved-jobs/").then(({data})=>setItems(data.results||data));},[]);return <><div className="dashboard-heading"><div><h1>Saved jobs</h1><p>Your shortlist of opportunities.</p></div></div>{items.length?items.map(x=><JobCard key={x.id} job={x.job_detail}/>):<div className="card empty">No saved jobs yet.</div>}</>}
