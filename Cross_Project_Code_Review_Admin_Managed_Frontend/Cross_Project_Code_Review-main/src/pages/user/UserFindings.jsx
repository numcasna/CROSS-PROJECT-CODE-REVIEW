import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Topbar from '../../components/Topbar'
import SeverityBadge from '../../components/SeverityBadge'
import StatusBadge from '../../components/StatusBadge'
import { useData } from '../../context/DataContext'
import { useAuth } from '../../context/AuthContext'
import { severityOrder, projectById, findingLabels } from '../../data/mockData'

function isOverdue(f){return Boolean(f.dueDate&&new Date(f.dueDate)<new Date()&&!['Closed','Rejected'].includes(f.status))}
const PAGE_SIZE=5
export default function UserFindings(){
 const {currentUser}=useAuth();const {findings}=useData();const navigate=useNavigate();const [status,setStatus]=useState('');const [severity,setSeverity]=useState('');const [label,setLabel]=useState('');const [overdueOnly,setOverdueOnly]=useState(false);const [page,setPage]=useState(1)
 const mine=findings.filter(f=>f.assignee===currentUser?.userId);const availableLabels=Array.from(new Set([...findingLabels,...findings.map(f=>f.label||f.category).filter(Boolean)]));const filtered=mine.filter(f=>(!status||f.status===status)&&(!severity||f.severity===severity)&&(!label||(f.label||'')===label)&&(!overdueOnly||isOverdue(f)));const pageCount=Math.max(1,Math.ceil(filtered.length/PAGE_SIZE));const safePage=Math.min(page,pageCount);const rows=filtered.slice((safePage-1)*PAGE_SIZE,safePage*PAGE_SIZE)
 useEffect(()=>setPage(1),[status,severity,label,overdueOnly])
 return <div><Topbar title="Findings"/><div className="page-container"><div className="page-header"><div><p className="eyebrow">FINDING WORKSPACE</p><h2>My Findings</h2><p>Work on findings created and assigned by the admin, then submit completed fixes for admin review.</p></div></div>
 <div className="filter-bar"><select value={status} onChange={e=>setStatus(e.target.value)}><option value="">All Statuses</option>{['Open','In Progress','Resolved','Reopened','Rejected','Closed'].map(s=><option key={s}>{s}</option>)}</select><select value={severity} onChange={e=>setSeverity(e.target.value)}><option value="">All Severities</option>{severityOrder.map(s=><option key={s}>{s}</option>)}</select><select value={label} onChange={e=>setLabel(e.target.value)}><option value="">All Labels</option>{availableLabels.map(s=><option key={s} value={s}>{s}</option>)}</select><label><input type="checkbox" checked={overdueOnly} onChange={e=>setOverdueOnly(e.target.checked)}/> Overdue only</label></div>
 <section className="table-card"><div className="table-heading"><div><h3>{filtered.length} assigned finding{filtered.length!==1?'s':''}</h3><p>Page {safePage} of {pageCount}</p></div></div><div className="table-wrap"><table><thead><tr><th>ID</th><th>Finding</th><th>Project</th><th>Label</th><th>Severity</th><th>Status</th><th>Accepted Date</th><th>Due Date</th></tr></thead><tbody>{rows.map(f=><tr key={f.id}><td className="muted-strong">{f.id}</td><td><button className="table-link" onClick={()=>navigate(`/user/findings/${f.id}`, { state: { from: '/user/findings', backLabel: 'Back to Findings' } })}>{f.title}</button></td><td>{projectById(f.project)?.name||f.project||'—'}</td><td>{f.label||'—'}</td><td><SeverityBadge severity={f.severity}/></td><td><StatusBadge status={f.status}/></td><td>{f.acceptedDate ? new Date(f.acceptedDate).toLocaleString() : 'Not accepted'}</td><td className={isOverdue(f)?'overdue-text':''}>{f.dueDate||'—'}</td></tr>)}{!rows.length&&<tr><td colSpan="8" className="empty-cell">No findings match these filters.</td></tr>}</tbody></table></div><div className="pagination"><button disabled={safePage===1} onClick={()=>setPage(p=>Math.max(1,p-1))}>Previous</button><span>Page {safePage} of {pageCount}</span><button disabled={safePage===pageCount} onClick={()=>setPage(p=>Math.min(pageCount,p+1))}>Next</button></div></section>
 </div></div>
}
