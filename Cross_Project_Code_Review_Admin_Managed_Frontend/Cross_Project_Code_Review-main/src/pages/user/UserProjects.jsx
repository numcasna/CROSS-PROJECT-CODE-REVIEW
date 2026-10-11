import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import Topbar from '../../components/Topbar'
import { useAuth } from '../../context/AuthContext'
import { useData } from '../../context/DataContext'
import { userById } from '../../data/mockData'
import Icon from '../../components/Icon'

export default function UserProjects() {
  const { currentUser } = useAuth()
  const { projects, findings } = useData()
  const navigate = useNavigate()
  const mine = useMemo(() => projects.filter((p) => p.members?.includes(currentUser?.userId)), [projects, currentUser])
  return <div><Topbar title="Projects"/><div className="page-container">
    <div className="page-header"><div><p className="eyebrow">WORKSPACE</p><h2>Your Projects</h2><p>View projects you belong to and all findings within each project.</p></div><button className="btn btn-primary" onClick={() => navigate('/user/projects/new')}>+ Create Project</button></div>
    <div className="project-grid">
      {mine.map((project) => <button type="button" className="project-card" key={project.id} onClick={() => navigate(`/user/projects/${project.id}`)}>
        <div className="project-card-top"><span className="project-icon"><Icon name="projects" size={18}/></span><span className="status-dot">{project.status}</span></div>
        <h3>{project.name}</h3><p>{project.description}</p>
        <div className="project-meta"><span>Lead: {userById(project.lead)?.name || '—'}</span><span>{findings.filter((f) => f.project === project.id).length} findings</span></div>
      </button>)}
      {!mine.length && <div className="empty-state">You are not a member of any projects.</div>}
    </div>
  </div></div>
}
