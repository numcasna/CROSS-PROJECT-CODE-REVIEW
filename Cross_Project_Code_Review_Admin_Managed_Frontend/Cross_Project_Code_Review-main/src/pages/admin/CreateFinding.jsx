import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Topbar from '../../components/Topbar'
import { useData } from '../../context/DataContext'
import { findingLabels, severityOrder, userById } from '../../data/mockData'
import { useAuth } from '../../context/AuthContext'

export default function CreateFinding() {
  const { addFinding, findings, projects, users } = useData()
  const { currentUser } = useAuth()
  const navigate = useNavigate()
  const isUser = currentUser?.role === 'user'
  const findingsPath = '/admin/findings'

  if (isUser) {
    navigate('/user/findings', { replace: true })
    return null
  }

  const [title, setTitle] = useState('')
  const [projectId, setProjectId] = useState('')
  const [repository, setRepository] = useState('')
  const [assignee, setAssignee] = useState('')
  const [severity, setSeverity] = useState('')
  const [label, setLabel] = useState('')
  const [dueDate, setDueDate] = useState('')
  const [description, setDescription] = useState('')
  const [recommendation, setRecommendation] = useState('')
  const [attachments, setAttachments] = useState([])
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const selectedProject = projects.find((p) => p.id === projectId)
  const nextId = `CR-${String(findings.length + 1).padStart(3, '0')}`

  function handleFileChange(e) {
    const files = Array.from(e.target.files || [])
    files.forEach((file) => {
      const allowed = /\.(jpe?g|pdf|txt)$/i.test(file.name)
      if (!allowed) { setError('Only JPG, PDF, and TXT evidence files are supported.'); return }
      const reader = new FileReader()
      reader.onload = () => {
        setAttachments((prev) => [
          ...prev,
          { name: file.name, type: file.type, size: file.size, dataUrl: reader.result, file },
        ])
      }
      reader.readAsDataURL(file)
    })
    e.target.value = '' // allow re-selecting the same file later
  }

  function removeAttachment(name) {
    setAttachments((prev) => prev.filter((a) => a.name !== name))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    if (!title.trim() || !projectId || !repository || !severity || !label || !dueDate || !description.trim()) {
      setError('Please fill in all required fields marked with *.')
      return
    }

    setSubmitting(true)
    try {
      const newFinding = await addFinding({
        title: title.trim(),
        project: projectId,
        repository,
        assignee: isUser ? currentUser?.userId : (assignee || null),
        severity,
        label,
        dueDate,
        description: description.trim(),
        recommendation: recommendation?.trim() || '',
        reviewer: currentUser?.userId || currentUser?.id,
        attachments,
      })

      const targetId = newFinding?.id || newFinding?.finding_code
      if (targetId) {
        navigate(`${findingsPath}/${targetId}`, { state: { from: findingsPath, backLabel: 'Back to Findings' } })
      } else {
        navigate(findingsPath)
      }
    } catch (err) {
      console.error('Failed to create finding:', err)
      setError(err?.message || 'Failed to create finding. Please verify all inputs.')
    } finally {
      setSubmitting(false)
    }
  }

  const getUser = (id) => (users || []).find((u) => u.id === id || u.userId === id) || userById(id)

  return (
    <div>
      <Topbar title="Create New Finding" />
      <div className="p-8 max-w-2xl">
        <div className="bg-white rounded-xl border border-gray-100 p-6">
          <button type="button" className="back-link mb-4" onClick={() => navigate(findingsPath)}>← Back to Findings</button><p className="text-sm text-gray-400 mb-6">New ID: <span className="text-accent font-medium">{nextId}</span></p>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Finding Title *</label>
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Brief description of the finding"
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/30"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Project *</label>
                <select
                  value={projectId}
                  onChange={(e) => { setProjectId(e.target.value); setRepository(''); setAssignee('') }}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
                >
                  <option value="">Select project...</option>
                  {projects.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Repository *</label>
                <select
                  value={repository}
                  onChange={(e) => setRepository(e.target.value)}
                  disabled={!selectedProject}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm disabled:bg-gray-50"
                >
                  <option value="">{selectedProject ? 'Select repository...' : 'Select project first'}</option>
                  {selectedProject?.repositories.map((r) => <option key={r.id || r.name} value={r.id || r.name}>{r.name}</option>)}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              {!isUser && <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Assignee</label>
                <select value={assignee} onChange={(e) => setAssignee(e.target.value)} disabled={!selectedProject} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm disabled:bg-gray-50">
                  <option value="">{selectedProject ? 'Unassigned' : 'Select project first'}</option>
                  {selectedProject && (() => {
                    const memberList = Array.from(new Set([
                      selectedProject.project_lead_id,
                      selectedProject.lead,
                      ...(selectedProject.members || []),
                    ])).filter(Boolean)
                    return memberList.map((mid) => {
                      const u = getUser(mid)
                      return (
                        <option key={mid} value={mid}>
                          {u?.name || 'User'}
                        </option>
                      )
                    })
                  })()}
                </select>
              </div>}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Severity *</label>
                <select
                  value={severity}
                  onChange={(e) => setSeverity(e.target.value)}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
                >
                  <option value="">Select severity...</option>
                  {severityOrder.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Finding Label *</label>
              <select
                value={label}
                onChange={(e) => setLabel(e.target.value)}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
              >
                <option value="">Select finding label...</option>
                {findingLabels.map((item) => (
                  <option key={item} value={item}>{item}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Due Date *</label>
              <input
                type="date"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Finding Description *</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={4}
                placeholder="Detail the finding, affected code, and potential impact..."
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
              />
            </div>

                        <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Feedback / Recommendation</label>
              <textarea
                value={recommendation}
                onChange={(e) => setRecommendation(e.target.value)}
                rows={3}
                placeholder="Actionable recommendations for fixing the issue..."
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Attachments</label>
              <input
                type="file"
                multiple
                accept=".jpg,.jpeg,.pdf,.txt,image/jpeg,application/pdf,text/plain"
                onChange={handleFileChange}
                className="w-full text-sm text-gray-600 file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-accent/10 file:text-accent hover:file:bg-accent/20"
              />
              <p className="text-xs text-gray-400 mt-1">Evidence files only: JPG, PDF, or TXT. You can select multiple files.</p>

              {attachments.length > 0 && (
                <ul className="mt-3 space-y-2">
                  {attachments.map((a) => (
                    <li key={a.name} className="flex items-center justify-between bg-gray-50 border border-gray-100 rounded-lg px-3 py-2 text-sm">
                      <div className="flex items-center gap-2 min-w-0">
                        {a.type.startsWith('image/') ? (
                          <img src={a.dataUrl} alt={a.name} className="w-8 h-8 object-cover rounded" />
                        ) : (
                          <span className="text-gray-400">📄</span>
                        )}
                        <span className="truncate text-gray-700">{a.name}</span>
                      </div>
                      <button type="button" onClick={() => removeAttachment(a.name)} className="text-gray-400 hover:text-red-500 text-xs ml-3 shrink-0">
                        Remove
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {error && <p className="text-red-500 text-sm">{error}</p>}

            <div className="flex gap-3 pt-2">
              <button type="submit" disabled={submitting} className="bg-accent hover:bg-accent-dark disabled:opacity-50 text-white text-sm font-medium px-5 py-2 rounded-lg">
                {submitting ? 'Creating Finding...' : 'Create Finding'}
              </button>
              <button type="button" onClick={() => navigate(findingsPath)} className="text-gray-500 text-sm font-medium px-5 py-2 rounded-lg border border-gray-200">
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
