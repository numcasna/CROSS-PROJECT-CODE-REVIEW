import { useState } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import Topbar from '../../components/Topbar'
import SeverityBadge from '../../components/SeverityBadge'
import StatusBadge from '../../components/StatusBadge'
import Icon from '../../components/Icon'
import FeedbackThread from '../../components/FeedbackThread'
import { useData } from '../../context/DataContext'
import { useAuth } from '../../context/AuthContext'
import { projectById, userById } from '../../data/mockData'

const USER_ALLOWED_STATUSES = ['In Progress']
function isOverdue(f) { return Boolean(f.dueDate && new Date(f.dueDate) < new Date() && !['Closed', 'Rejected'].includes(f.status)) }

export default function UserFindingDetail() {
  const { id } = useParams(); const navigate = useNavigate(); const location = useLocation()
  const { findings, projects, updateFindingStatus } = useData(); const { currentUser } = useAuth()
  if (!id || id === 'undefined') {
    navigate('/user/findings', { replace: true })
    return null
  }

  const finding = findings.find((f) => f.id === id || f.code === id || f.displayId === id || f.finding_code === id)
  const project = finding ? (projects.find((p) => p.id === finding.project) || projectById(finding.project)) : null
  const isProjectMember = Boolean(project?.members?.includes(currentUser?.userId))
  const isAssignee = finding?.assignee === currentUser?.userId
  const [feedback, setFeedback] = useState(''); const [attachments, setAttachments] = useState([]); const [error, setError] = useState('')

  if (!finding || !isProjectMember) return <div><Topbar title="Finding Details"/><div className="page-container"><div className="empty-state">This finding is not available to your account.</div></div></div>

  const canSubmitForReview = isAssignee && USER_ALLOWED_STATUSES.includes(finding.status)
  const canAccept = isAssignee && finding.status === 'Open'
  const canResume = isAssignee && finding.status === 'Reopened'
  const overdue = isOverdue(finding)
  const backTarget = location.state?.from
  const backLabel = location.state?.backLabel || 'Back'

  function goBack() { if (backTarget) navigate(backTarget); else navigate(-1) }
  function handleFileChange(e) { Array.from(e.target.files || []).forEach((file) => { if (!/\.(jpe?g|pdf|txt)$/i.test(file.name)) { setError('Only JPG, PDF, and TXT evidence files are supported.'); return } const reader = new FileReader(); reader.onload = () => setAttachments((prev) => [...prev,{name:file.name,type:file.type,size:file.size,dataUrl:reader.result}]); reader.readAsDataURL(file) }); e.target.value='' }
  function acceptFinding() { updateFindingStatus(finding.id, 'In Progress', currentUser.name, '', [], 'user') }
  function resumeFinding() { updateFindingStatus(finding.id, 'In Progress', currentUser.name, 'Work resumed after the finding was reopened.', [], 'user') }
  function submitForReview() { const note=feedback.trim(); if(!note){setError('Please describe the fix and validation before submitting for review.');return} updateFindingStatus(finding.id,'In Review',currentUser.name,note,attachments,'user'); setFeedback('');setAttachments([]);setError('') }

  return <div><Topbar title="Finding Details"/><div className="page-container" style={{maxWidth:1040}}>
    <button className="back-link" onClick={goBack}>← {backLabel}</button>
    <section className="detail-card">
      <div className="detail-title-row"><div><div className="finding-id-line"><span>{finding.id}</span>{overdue&&<span className="overdue-badge">Overdue</span>}</div><h2>{finding.title}</h2></div><SeverityBadge severity={finding.severity}/></div>
      {!isAssignee && <div className="read-only-notice">You are viewing a teammate's finding. Project membership gives you view access only; assignment, severity, label, status and admin actions cannot be changed here.</div>}
      <div className="info-grid finding-info"><div><span>Project</span><strong>{project?.name || finding.project || '—'}</strong></div><div><span>Repository</span><strong>{finding.repository || '—'}</strong></div><div><span>Finding Label</span><strong>{finding.label || '—'}</strong></div><div><span>Status</span><strong><StatusBadge status={finding.status}/></strong></div></div>
      <div className="info-grid finding-info"><div><span>Created Date</span><strong>{finding.created || '—'}</strong></div><div><span>Accepted Date</span><strong>{finding.acceptedDate ? new Date(finding.acceptedDate).toLocaleString() : 'Not accepted'}</strong></div><div><span>Due Date</span><strong className={overdue?'overdue-text':''}>{finding.dueDate || '—'}</strong></div><div><span>Reviewer</span><strong>{userById(finding.reviewer)?.name || finding.reviewer || '—'}</strong></div></div>
      {canAccept && <div className="action-banner"><div><strong>Ready to start?</strong><span>Accepting this finding moves it from Open to In Progress and records the Accepted Date.</span></div><button className="btn btn-primary" onClick={acceptFinding}><Icon name="check" size={16}/> Accept</button></div>}
      {canResume && <div className="action-banner"><div><strong>This finding was reopened</strong><span>Resume work to move it back to In Progress. Once fixed, submit it for admin review.</span></div><button className="btn btn-primary" onClick={resumeFinding}><Icon name="check" size={16}/> Resume Work</button></div>}
      {finding.status === 'In Review' && <div className="read-only-notice">Submitted for admin review. You cannot mark a finding as Resolved; an admin will accept the fix or reopen it with feedback.</div>}
    </section>

    <section className="detail-card detail-section-card"><h3>Finding Description</h3><p className="detail-copy">{finding.description || '—'}</p></section>
    <section className="detail-card detail-section-card recommendation"><h3>Feedback / Recommendation</h3><p className="detail-copy">{finding.recommendation || '—'}</p></section>

    <section className="detail-card detail-section-card"><div className="section-heading"><div><h3>Feedback Thread</h3><p className="helper">Chronological feedback, status decisions, responses and associated attachments.</p></div></div><FeedbackThread finding={finding}/></section>

    {canSubmitForReview && <section className="detail-card detail-section-card"><h3>Submit for Admin Review</h3><p className="helper">Explain the fix and validation. Submission moves this finding to In Review; only an admin can mark it Resolved.</p><textarea value={feedback} onChange={(e)=>{setFeedback(e.target.value);if(e.target.value.trim())setError('')}} rows={4} placeholder="Describe the fix, validation, test results, or remaining context..." className="field-textarea"/>
      <label className="file-input-label">Evidence attachments (JPG, PDF, TXT)<input type="file" multiple accept=".jpg,.jpeg,.pdf,.txt,image/jpeg,text/plain,application/pdf" onChange={handleFileChange}/></label>
      {attachments.length>0&&<div className="attachment-list">{attachments.map((a)=><div key={a.name}><Icon name="file" size={16}/><span>{a.name}</span><button type="button" onClick={()=>setAttachments((p)=>p.filter(x=>x.name!==a.name))}>Remove</button></div>)}</div>}
      {error&&<p className="form-error">{error}</p>}<button className="btn btn-primary" type="button" onClick={submitForReview}>Submit for Review</button>
    </section>}

    {finding.attachments?.length>0&&<section className="detail-card detail-section-card"><h3>Attachments</h3><div className="attachment-list">{finding.attachments.map((a)=><a key={a.name} href={a.dataUrl} download={a.name}><Icon name="file" size={16}/><span>{a.name}</span></a>)}</div></section>}
  </div></div>
}
