import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Topbar from '../../components/Topbar'
import SeverityBadge from '../../components/SeverityBadge'
import StatusBadge from '../../components/StatusBadge'
import { useData } from '../../context/DataContext'
import { findingLabels, severityOrder, statusOrder, projectById } from '../../data/mockData'

const PAGE_SIZE = 5

function Select({ value, onChange, options, placeholder }) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 bg-white text-gray-600 focus:outline-none focus:ring-2 focus:ring-accent/30"
    >
      <option value="">{placeholder}</option>
      {options.map((o) => {
        const value = typeof o === 'string' ? o : o.value
        const label = typeof o === 'string' ? o : o.label
        return <option key={value} value={value}>{label}</option>
      })}
    </select>
  )
}

function isOverdue(finding) {
  return Boolean(
    finding.dueDate &&
    new Date(finding.dueDate) < new Date() &&
    !['Closed', 'Rejected'].includes(finding.status),
  )
}

export default function AdminFindings() {
  const { findings, projects } = useData()
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [project, setProject] = useState('')
  const [severity, setSeverity] = useState('')
  const [label, setLabel] = useState('')
  const [status, setStatus] = useState('')
  const [overdueOnly, setOverdueOnly] = useState(false)
  const [page, setPage] = useState(1)

  const availableLabels = useMemo(() => {
    const fromFindings = findings.map((f) => f.label || f.category).filter(Boolean)
    return Array.from(new Set([...findingLabels, ...fromFindings]))
  }, [findings])

  const filtered = useMemo(() => findings.filter((f) => {
    const query = search.trim().toLowerCase()
    if (query && !f.title.toLowerCase().includes(query) && !f.id.toLowerCase().includes(query)) return false
    if (project && f.project !== project) return false
    if (severity && f.severity !== severity) return false
    if (label && (f.label || '') !== label) return false
    if (status && f.status !== status) return false
    if (overdueOnly && !isOverdue(f)) return false
    return true
  }), [findings, search, project, severity, label, status, overdueOnly])

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const safePage = Math.min(page, pageCount)
  const pageFindings = filtered.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE)

  useEffect(() => {
    setPage(1)
  }, [search, project, severity, label, status, overdueOnly])

  return (
    <div>
      <Topbar title="Findings" search={search} onSearchChange={setSearch} />
      <div className="p-8">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <div className="flex flex-wrap items-center gap-2">
            <Select value={project} onChange={setProject} placeholder="All Projects" options={projects.map((p) => ({ value: p.id, label: p.name }))} />
            <Select value={severity} onChange={setSeverity} placeholder="All Severities" options={severityOrder} />
            <Select value={label} onChange={setLabel} placeholder="All Finding Labels" options={availableLabels} />
            <Select value={status} onChange={setStatus} placeholder="All Statuses" options={statusOrder} />
            <label className="flex items-center gap-1.5 text-sm text-gray-500">
              <input type="checkbox" checked={overdueOnly} onChange={(e) => setOverdueOnly(e.target.checked)} />
              Overdue only
            </label>
          </div>
          <button type="button" onClick={() => navigate('/admin/findings/new')} className="btn btn-primary">＋ Create Finding</button>
        </div>

        <div className="bg-white rounded-xl border border-gray-100 overflow-x-auto">
          <p className="px-5 py-3 text-sm text-gray-400 border-b border-gray-100">
            {filtered.length} finding{filtered.length !== 1 ? 's' : ''} · Page {safePage} of {pageCount}
          </p>
          <table className="w-full text-sm min-w-[950px]">
            <thead>
              <tr className="text-left text-xs text-gray-400">
                <th className="px-5 py-2 font-medium">ID</th>
                <th className="px-5 py-2 font-medium">Title</th>
                <th className="px-5 py-2 font-medium">Project</th>
                <th className="px-5 py-2 font-medium">Finding Label</th>
                <th className="px-5 py-2 font-medium">Severity</th>
                <th className="px-5 py-2 font-medium">Status</th>
                <th className="px-5 py-2 font-medium">Created Date</th>
                <th className="px-5 py-2 font-medium">Due Date</th>
              </tr>
            </thead>
            <tbody>
              {pageFindings.map((f) => (
                <tr key={f.id} className="border-t border-gray-50 hover:bg-gray-50">
                  <td className="px-5 py-2.5 text-accent font-medium whitespace-nowrap">{f.id}</td>
                  <td className="px-5 py-2.5 max-w-[260px]">
                    <button
                      type="button"
                      onClick={() => navigate(`/admin/findings/${f.id}`, { state: { from: '/admin/findings', backLabel: 'Back to Findings' } })}
                      className="text-accent font-medium text-left hover:underline truncate block max-w-[260px]"
                      title={f.title}
                    >
                      {f.title}
                    </button>
                  </td>
                  <td className="px-5 py-2.5 text-gray-500 whitespace-nowrap">{projectById(f.project)?.name || f.project || '—'}</td>
                  <td className="px-5 py-2.5 whitespace-nowrap">
                    {f.label ? (
                      <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded-full text-xs">{f.label}</span>
                    ) : <span className="text-gray-300">—</span>}
                  </td>
                  <td className="px-5 py-2.5"><SeverityBadge severity={f.severity} /></td>
                  <td className="px-5 py-2.5"><StatusBadge status={f.status} /></td>
                  <td className="px-5 py-2.5 text-gray-500 whitespace-nowrap">{f.created || '—'}</td>
                  <td className={`px-5 py-2.5 whitespace-nowrap ${isOverdue(f) ? 'text-red-600 font-medium' : 'text-gray-500'}`}>
                    {f.dueDate || '—'}
                  </td>
                </tr>
              ))}
              {pageFindings.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-5 py-8 text-center text-gray-400">No findings match these filters.</td>
                </tr>
              )}
            </tbody>
          </table>

          <div className="flex items-center justify-center gap-4 px-5 py-4 border-t border-gray-100">
            <button
              type="button"
              disabled={safePage === 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="text-sm font-medium text-gray-600 disabled:text-gray-300"
            >
              Previous
            </button>
            <span className="text-sm text-gray-500">Page {safePage} of {pageCount}</span>
            <button
              type="button"
              disabled={safePage === pageCount}
              onClick={() => setPage((p) => Math.min(pageCount, p + 1))}
              className="text-sm font-medium text-gray-600 disabled:text-gray-300"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
