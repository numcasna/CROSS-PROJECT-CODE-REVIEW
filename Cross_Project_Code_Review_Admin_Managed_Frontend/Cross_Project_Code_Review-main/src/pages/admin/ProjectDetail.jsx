import { useParams, useNavigate } from 'react-router-dom'
import Topbar from '../../components/Topbar'
import Avatar from '../../components/Avatar'
import SeverityBadge from '../../components/SeverityBadge'
import StatusBadge from '../../components/StatusBadge'
import { useData } from '../../context/DataContext'
import { userById } from '../../data/mockData'

export default function ProjectDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { projects, findings } = useData()
  const project = projects.find((p) => p.id === id)

  if (!project) {
    return (
      <div>
        <Topbar title="Project" />
        <div className="p-8">Project not found.</div>
      </div>
    )
  }

  const projectFindings = findings.filter((f) => f.project === id)
  const counts = ['Open', 'In Progress', 'Resolved', 'Rejected', 'Closed'].map((s) => ({
    label: s,
    count: projectFindings.filter((f) => f.status === s).length,
  }))
  const lead = userById(project.lead)

  return (
    <div>
      <Topbar title={project.name} />
      <div className="p-8">
        <button onClick={() => navigate('/admin/projects')} className="back-link">← Back to Projects</button>

        <div className="bg-white rounded-xl border border-gray-100 p-6 mb-6">
          <div className="flex items-start justify-between mb-1">
            <p className="text-lg font-semibold text-gray-800">{project.name}</p>
            <span className="bg-green-100 text-green-700 text-xs px-2 py-0.5 rounded-full">{project.status}</span>
          </div>
          <p className="text-sm text-gray-500 mb-3">{project.description}</p>
          {lead && <p className="text-xs text-gray-400">Project Lead: <span className="text-gray-700 font-medium">{lead.name}</span></p>}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-6">
          <div className="bg-white rounded-xl border border-gray-100 p-5">
            <p className="text-sm font-medium text-gray-700 mb-3">Repositories ({project.repositories.length})</p>
            <ul className="space-y-2">
              {project.repositories.map((r) => (
                <li key={r.name} className="flex items-center justify-between text-sm">
                  <span className="text-accent flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-accent" />{r.name}</span>
                  <span className="text-gray-400 text-xs">{r.findings} findings</span>
                </li>
              ))}
              {project.repositories.length === 0 && <p className="text-sm text-gray-400">No repositories yet.</p>}
            </ul>
          </div>

          <div className="bg-white rounded-xl border border-gray-100 p-5">
            <p className="text-sm font-medium text-gray-700 mb-3">Members ({project.members.length})</p>
            <ul className="space-y-3">
              {project.members.map((mid) => {
                const u = userById(mid)
                if (!u) return null
                return (
                  <li key={mid} className="flex items-center gap-3">
                    <Avatar user={u} />
                    <div>
                      <p className="text-sm text-gray-700 leading-tight">{u.name}{mid === project.lead && <span className="ml-2 text-xs bg-accent/10 text-accent px-1.5 py-0.5 rounded">Lead</span>}</p>
                      <p className="text-xs text-gray-400 leading-tight">{u.role}</p>
                    </div>
                  </li>
                )
              })}
              {project.members.length === 0 && <p className="text-sm text-gray-400">No members yet.</p>}
            </ul>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-100">
          <div className="px-5 py-4 border-b border-gray-100">
            <p className="text-sm font-medium text-gray-700 mb-3">Project Findings ({projectFindings.length})</p>
            <div className="flex flex-wrap gap-6">
              {counts.map((c) => (
                <div key={c.label} className="text-center">
                  <p className="text-lg font-semibold text-gray-800">{c.count}</p>
                  <p className="text-xs text-gray-400">{c.label}</p>
                </div>
              ))}
            </div>
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-gray-400">
                <th className="px-5 py-2 font-medium">ID</th>
                <th className="px-5 py-2 font-medium">Title</th>
                <th className="px-5 py-2 font-medium">Severity</th>
                <th className="px-5 py-2 font-medium">Status</th>
                <th className="px-5 py-2 font-medium">Assignee</th>
              </tr>
            </thead>
            <tbody>
              {projectFindings.map((f) => (
                <tr key={f.id} onClick={() => navigate(`/admin/findings/${f.id}`, { state: { from: `/admin/projects/${id}`, backLabel: 'Back to Project' } })} className="border-t border-gray-50 hover:bg-gray-50 cursor-pointer">
                  <td className="px-5 py-2.5 text-accent font-medium">{f.id}</td>
                  <td className="px-5 py-2.5 text-gray-700">{f.title}</td>
                  <td className="px-5 py-2.5"><SeverityBadge severity={f.severity} /></td>
                  <td className="px-5 py-2.5"><StatusBadge status={f.status} /></td>
                  <td className="px-5 py-2.5 text-gray-500">{userById(f.assignee)?.name || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
