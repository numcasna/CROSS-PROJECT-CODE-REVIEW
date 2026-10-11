import { useNavigate } from 'react-router-dom'
import Topbar from '../../components/Topbar'
import { useData } from '../../context/DataContext'
import { userById } from '../../data/mockData'

const STATUS_STYLES = {
  Active: 'bg-green-100 text-green-700',
  'On Hold': 'bg-yellow-100 text-yellow-700',
}

export default function AdminProjects() {
  const { projects, findings } = useData()
  const navigate = useNavigate()

  return (
    <div>
      <Topbar title="Projects" search="" onSearchChange={() => {}} />
      <div className="p-8">
        <p className="text-sm text-gray-500 mb-5">Read-only view of every project and its full details. Project creation and editing are available only to users.</p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          {projects.map((p) => {
            const projectFindings = findings.filter((f) => f.project === p.id)
            const lead = userById(p.lead)
            return (
              <button
                key={p.id}
                onClick={() => navigate(`/admin/projects/${p.id}`)}
                className="text-left bg-white rounded-xl border border-gray-100 p-5 hover:shadow-sm transition-shadow"
              >
                <div className="flex items-start justify-between mb-1">
                  <p className="font-semibold text-gray-800">{p.name}</p>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${STATUS_STYLES[p.status] || 'bg-gray-100 text-gray-600'}`}>{p.status}</span>
                </div>
                <p className="text-sm text-gray-500 mb-3">{p.description}</p>
                <p className="text-xs text-gray-400 mb-3">
                  {p.repositories.length} repos &nbsp;·&nbsp; {p.members.length} members &nbsp;·&nbsp; {projectFindings.length} findings
                </p>
                {lead && (
                  <p className="text-xs text-gray-400">
                    Lead: <span className="text-gray-600 font-medium">{lead.name}</span>
                  </p>
                )}
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}
