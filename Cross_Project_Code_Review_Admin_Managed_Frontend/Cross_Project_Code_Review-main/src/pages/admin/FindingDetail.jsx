import { useParams, useNavigate, useLocation } from 'react-router-dom'
import Topbar from '../../components/Topbar'
import SeverityBadge from '../../components/SeverityBadge'
import StatusBadge from '../../components/StatusBadge'
import FeedbackThread from '../../components/FeedbackThread'
import { useData } from '../../context/DataContext'
import { useState } from 'react'
import { useAuth } from '../../context/AuthContext'
import { projectById, userById } from '../../data/mockData'

function isOverdue(finding) {
  return Boolean(finding.dueDate && new Date(finding.dueDate) < new Date() && !['Closed', 'Rejected'].includes(finding.status))
}

export default function FindingDetail() {
  const { id } = useParams(); const navigate = useNavigate(); const location = useLocation(); const { findings, updateFindingStatus, loading } = useData(); const { currentUser } = useAuth(); const [decisionNote, setDecisionNote] = useState(''); const [decisionError, setDecisionError] = useState('')

  if (!id || id === 'undefined') {
    navigate('/admin/findings', { replace: true })
    return null
  }

  const finding = findings.find((f) => f.id === id || f.code === id || f.displayId === id || f.finding_code === id)

  if (!finding) {
    if (loading) {
      return <div><Topbar title="Finding Details"/><div className="page-container"><p className="text-gray-500">Loading finding details...</p></div></div>
    }
    return <div><Topbar title="Finding Details"/><div className="page-container"><p className="text-gray-500">Finding {id} was not found.</p><button onClick={() => navigate(-1)} className="back-link">← Back</button></div></div>
  }

  const overdue = isOverdue(finding)
  const backTarget = location.state?.from
  const backLabel = location.state?.backLabel || 'Back'
  const goBack = () => backTarget ? navigate(backTarget) : navigate(-1)

  return <div><Topbar title="Finding Details"/><div className="page-container" style={{maxWidth:1040}}>
    <button onClick={goBack} className="back-link">← {backLabel}</button>
    <section className="detail-card">
      <div className="detail-title-row"><div><div className="finding-id-line"><span>{finding.id}</span><span className="muted-date">Created {finding.created || '—'}</span>{overdue&&<span className="overdue-badge">Overdue</span>}</div><h2>{finding.title}</h2></div><SeverityBadge severity={finding.severity}/></div>
      <div className="info-grid finding-info"><div><span>Project</span><strong>{projectById(finding.project)?.name || finding.project || '—'}</strong></div><div><span>Repository</span><strong>{finding.repository || '—'}</strong></div><div><span>Finding Label</span><strong>{finding.label || '—'}</strong></div><div><span>Status</span><strong><StatusBadge status={finding.status}/></strong></div></div>
      <div className="info-grid finding-info"><div><span>Created Date</span><strong>{finding.created || '—'}</strong></div><div><span>Accepted Date</span><strong>{finding.acceptedDate ? new Date(finding.acceptedDate).toLocaleString() : 'Not accepted'}</strong></div><div><span>Due Date</span><strong className={overdue?'overdue-text':''}>{finding.dueDate || '—'}</strong></div><div><span>Reviewer</span><strong>{userById(finding.reviewer)?.name || finding.reviewer || '—'}</strong></div></div>
    </section>
    {['In Review', 'Resolved'].includes(finding.status) && <section className="detail-card detail-section-card">
      <h3>Admin Decision</h3><p className="helper">Record a reason for the status decision. Reopen, reject, and close actions are available for resolved findings.</p>
      <textarea value={decisionNote} onChange={e => {setDecisionNote(e.target.value);setDecisionError('')}} rows={3} className="field-textarea" placeholder="Add review feedback or reason (required)..." />
      {decisionError && <p className="form-error">{decisionError}</p>}
      <div className="flex flex-wrap gap-2 mt-3">
        {finding.status === 'In Review' && <button className="btn btn-primary" onClick={() => {if(!decisionNote.trim()){setDecisionError('A review note is required.');return} if(updateFindingStatus(finding.id,'Resolved',currentUser.name,decisionNote,[],'admin')){setDecisionNote('');setDecisionError('')}}}>Resolve Finding</button>}
        {finding.status === 'In Review' && <button className="btn" onClick={() => {if(!decisionNote.trim()){setDecisionError('A reason is required to reopen.');return} if(updateFindingStatus(finding.id,'Reopened',currentUser.name,decisionNote,[],'admin')){setDecisionNote('');setDecisionError('')}}}>Reopen</button>}
        {finding.status === 'Resolved' && <><button className="btn" onClick={() => {if(!decisionNote.trim()){setDecisionError('A reason is required to reopen.');return} if(updateFindingStatus(finding.id,'Reopened',currentUser.name,decisionNote,[],'admin')){setDecisionNote('');setDecisionError('')}}}>Reopen</button><button className="btn" onClick={() => {if(!decisionNote.trim()){setDecisionError('A rejection reason is required.');return} if(updateFindingStatus(finding.id,'Rejected',currentUser.name,decisionNote,[],'admin')){setDecisionNote('');setDecisionError('')}}}>Reject</button><button className="btn" onClick={() => {if(!decisionNote.trim()){setDecisionError('A closing reason is required.');return} if(updateFindingStatus(finding.id,'Closed',currentUser.name,decisionNote,[],'admin')){setDecisionNote('');setDecisionError('')}}}>Close</button></>}
      </div>
    </section>}
    <section className="detail-card detail-section-card"><h3>Finding Description</h3><p className="detail-copy">{finding.description || '—'}</p></section>
    <section className="detail-card detail-section-card recommendation"><h3>Feedback / Recommendation</h3><p className="detail-copy">{finding.recommendation || '—'}</p></section>
    <section className="detail-card detail-section-card"><div className="section-heading"><div><h3>Feedback & History</h3><p className="helper">Complete chronological discussion, status decisions and attachments.</p></div></div><FeedbackThread finding={finding}/></section>
    {finding.attachments?.length>0&&<section className="detail-card detail-section-card"><h3>Current Attachments</h3><div className="attachment-list">{finding.attachments.map((a)=><a key={a.name} href={a.dataUrl} download={a.name}><span>{a.name}</span></a>)}</div></section>}
  </div></div>
}
