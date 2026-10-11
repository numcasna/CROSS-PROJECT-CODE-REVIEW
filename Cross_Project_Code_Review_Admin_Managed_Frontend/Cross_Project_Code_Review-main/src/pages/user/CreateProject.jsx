import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Topbar from '../../components/Topbar'
import { useData } from '../../context/DataContext'
import { useAuth } from '../../context/AuthContext'
import { users } from '../../data/mockData'

export default function CreateProject() {
  const navigate = useNavigate()
  const { addProject } = useData()
  const { currentUser } = useAuth()
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [status, setStatus] = useState('Active')
  const [members, setMembers] = useState([currentUser?.userId].filter(Boolean))
  const [repositoryCount, setRepositoryCount] = useState(1)
  const [repositories, setRepositories] = useState([''])
  const [error, setError] = useState('')

  function toggleMember(id) {
    setMembers(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id])
  }
  function changeRepositoryCount(value) {
    const count = Math.max(1, Math.min(30, Number(value) || 1))
    setRepositoryCount(count)
    setRepositories(prev => Array.from({ length: count }, (_, i) => prev[i] || ''))
  }
  function updateRepository(index, value) {
    setRepositories(prev => prev.map((repo, i) => i === index ? value : repo))
  }
  function submit(e) {
    e.preventDefault()
    setError('')
    if (!name.trim()) return setError('Project name is required.')
    if (!members.length) return setError('Select at least one project member.')
    const repoNames = repositories.map(repo => repo.trim())
    if (repoNames.some(repo => !repo)) return setError('Enter a name for every repository, or reduce the repository count.')
    if (new Set(repoNames.map(repo => repo.toLowerCase())).size !== repoNames.length) return setError('Repository names must be unique.')
    const project = addProject({
      name: name.trim(), description: description.trim(), status,
      lead: currentUser?.userId || members[0], members,
      repositories: repoNames.map(repoName => ({ name: repoName, findings: 0 })),
      createdBy: currentUser?.userId,
    })
    navigate(`/user/projects/${project.id}`)
  }

  return <div>
    <Topbar title="Create Project" />
    <div className="page-container" style={{ maxWidth: 920 }}>
      <button className="back-link" onClick={() => navigate('/user/projects')}>← Back to Projects</button>
      <section className="detail-card detail-section-card">
        <div className="mb-6">
          <p className="eyebrow">PROJECT SETUP</p>
          <h2 className="text-2xl font-semibold mb-2">Create a Project</h2>
          <p className="helper">Set up the project workspace, list its repositories, and choose the people who should have access. Admins can view project details but cannot create or edit projects.</p>
        </div>
        <form onSubmit={submit} className="space-y-6">
          <section className="rounded-xl border border-gray-100 bg-gray-50 p-4 space-y-4">
            <h3 className="font-semibold text-gray-800">1. Project details</h3>
            <div><label className="field-label">Project Name *</label><input value={name} onChange={e => setName(e.target.value)} className="field-input" placeholder="e.g. Customer Portal" required /></div>
            <div><label className="field-label">Description</label><textarea value={description} onChange={e => setDescription(e.target.value)} rows={4} className="field-textarea" placeholder="Describe the project purpose, scope, and key goals." /></div>
            <div><label className="field-label">Project Status</label><select value={status} onChange={e => setStatus(e.target.value)} className="field-input"><option>Active</option><option>On Hold</option></select></div>
          </section>

          <section className="rounded-xl border border-gray-100 p-4 space-y-4">
            <div><h3 className="font-semibold text-gray-800">2. Repositories</h3><p className="helper mt-1">Choose how many repositories belong to this project, then enter each repository name separately.</p></div>
            <div style={{ maxWidth: 260 }}><label className="field-label">Number of repositories *</label><input type="number" min="1" max="30" value={repositoryCount} onChange={e => changeRepositoryCount(e.target.value)} className="field-input" required /><p className="helper mt-1">Enter between 1 and 30 repositories.</p></div>
            <div className="grid md:grid-cols-2 gap-4">{repositories.map((repo, index) => <div key={index}><label className="field-label">Repository {index + 1} name *</label><input value={repo} onChange={e => updateRepository(index, e.target.value)} className="field-input" placeholder={index === 0 ? 'e.g. customer-portal-api' : `repository-${index + 1}`} required /></div>)}</div>
          </section>

          <section className="rounded-xl border border-gray-100 p-4 space-y-3">
            <h3 className="font-semibold text-gray-800">3. Project members *</h3>
            <p className="helper">Select all users who should be able to view project findings. You are included by default.</p>
            <div className="grid sm:grid-cols-2 gap-2">{users.map(user => <label key={user.id} className="flex items-center gap-2 rounded-lg border border-gray-200 p-3 text-sm bg-white"><input type="checkbox" checked={members.includes(user.id)} onChange={() => toggleMember(user.id)} /><span>{user.name}</span>{user.id === currentUser?.userId && <span className="you-badge">You</span>}</label>)}</div>
          </section>

          {error && <p className="form-error">{error}</p>}
          <div className="flex flex-wrap items-center justify-between gap-3 border-t border-gray-100 pt-5"><p className="helper">Fields marked * are required.</p><div className="flex gap-3"><button type="button" className="btn" onClick={() => navigate('/user/projects')}>Cancel</button><button type="submit" className="btn btn-primary">Create Project</button></div></div>
        </form>
      </section>
    </div>
  </div>
}
