import { useNavigate, useParams } from 'react-router-dom'
import Topbar from '../../components/Topbar'
import SeverityBadge from '../../components/SeverityBadge'
import StatusBadge from '../../components/StatusBadge'
import Avatar from '../../components/Avatar'
import { useAuth } from '../../context/AuthContext'
import { useData } from '../../context/DataContext'
import { projectById, userById } from '../../data/mockData'

function isOverdue(f) {
  return Boolean(f.dueDate && new Date(f.dueDate) < new Date() && !['Closed', 'Rejected'].includes(f.status))
}

export default function UserProjectDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { currentUser } = useAuth()
  const { projects, findings } = useData()
  const project = projectById(id) || projects.find((p) => p.id === id)

  if (!project || !project.members?.includes(currentUser?.userId)) {
    return <div><Topbar title="Project" /><div className="page-container"><div className="empty-state">This project is not available to your account.</div></div></div>
  }

  const projectFindings = findings.filter((f) => f.project === project.id).sort((a, b) => new Date(b.created || 0) - new Date(a.created || 0))
  const myFindings = projectFindings.filter((f) => f.assignee === currentUser?.userId).length

  return <div><Topbar title="Project Details" /><div className="page-container">
    <button className="back-link" onClick={() => navigate('/user/projects')}>← Back to Projects</button>
    <section className="detail-card project-detail-card">
      <div className="detail-title-row"><div><p className="eyebrow">PROJECT</p><h2>{project.name}</h2><p>{project.description}</p></div><span className="status-pill">{project.status}</span></div>
      <div className="info-grid">
        <div><span>Project Lead</span><strong>{userById(project.lead)?.name || '—'}</strong></div>
        <div><span>Repositories</span><strong>{project.repositories?.length || 0}</strong></div>
        <div><span>Members</span><strong>{project.members?.length || 0}</strong></div>
        <div><span>Project Findings</span><strong>{projectFindings.length}</strong></div>
        <div><span>Your Findings</span><strong>{myFindings}</strong></div>
      </div>
      <div className="detail-section"><h3>Repositories</h3><div className="repo-list">{project.repositories?.map((repo) => <div key={repo.name} className="repo-row"><span>{repo.name}</span><span>{projectFindings.filter((f) => f.repository === repo.name).length} findings</span></div>)}</div></div>
      <div className="detail-section"><h3>Members</h3><div className="member-list">{project.members?.map((member) => { const u = userById(member); return <span key={member} className="member-chip"><Avatar user={u} size={24}/>{u?.name || member}</span> })}</div></div>
    </section>

    <section className="table-card">
      <div className="table-heading"><div><h3>All Project Findings</h3><p>You can view every finding in this project, including findings assigned to teammates. Editing and workflow actions remain restricted to authorized users.</p></div></div>
      <div className="table-wrap"><table><thead><tr><th>ID</th><th>Finding</th><th>Label</th><th>Severity</th><th>Status</th><th>Assigned To</th><th>Created Date</th><th>Accepted Date</th><th>Due Date</th></tr></thead><tbody>
        {projectFindings.map((f) => <tr key={f.id}>
          <td className="muted-strong">{f.id}</td>
          <td><button className="table-link" onClick={() => navigate(`/user/findings/${f.id}`, { state: { from: `/user/projects/${project.id}`, backLabel: 'Back to Project' } })}>{f.title}</button></td>
          <td>{f.label || '—'}</td><td><SeverityBadge severity={f.severity}/></td><td><StatusBadge status={f.status}/></td>
          <td>{userById(f.assignee)?.name || 'Unassigned'}{f.assignee === currentUser?.userId && <span className="you-badge">You</span>}</td><td>{f.created || '—'}</td><td>{f.acceptedDate ? new Date(f.acceptedDate).toLocaleString() : 'Not accepted'}</td>
          <td className={isOverdue(f) ? 'overdue-text' : ''}>{f.dueDate || '—'}</td>
        </tr>)}
        {!projectFindings.length && <tr><td colSpan="9" className="empty-cell">No findings in this project.</td></tr>}
      </tbody></table></div>
    </section>
  </div></div>
}
