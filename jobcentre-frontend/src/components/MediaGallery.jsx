import { FileText } from "lucide-react";
export default function MediaGallery({media=[]}) {
  if (!media.length) return null;
  return <div className="media-gallery">{media.map(item => item.media_type === "image" ? <img key={item.id} src={item.file} alt={item.caption || "Job attachment"}/> : item.media_type === "video" ? <video key={item.id} controls preload="metadata"><source src={item.file}/></video> : <a key={item.id} className="pdf-link" href={item.file} target="_blank" rel="noreferrer"><FileText/>View attached PDF</a>)}</div>;
}
