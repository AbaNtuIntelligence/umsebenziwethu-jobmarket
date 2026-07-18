import {ChevronRight} from "lucide-react";
import {useEffect,useState} from "react";
import {Link} from "react-router-dom";
import api from "../services/api";
export default function ApplicationsPage(){const [items,setItems]=useState([]);useEffect(()=>{api.get("/applications/").then(({data})=>setItems(data.results||data));},[]);return <><div className="dashboard-heading"><div><h1>Applications</h1><p>Every submission has a reference and permanent status history.</p></div></div>{items.length?items.map(x=><Link className="list-card application-list-item" to={`/applications/${x.id}`} key={x.id}><div><b>{x.job_title}</b><small>{x.reference} · Submitted {new Date(x.created_at).toLocaleDateString("en-ZA")}</small></div><span className={`status ${x.status}`}>{x.status}</span><ChevronRight/></Link>):<div className="card empty">You have not applied for a job yet.</div>}</>}
