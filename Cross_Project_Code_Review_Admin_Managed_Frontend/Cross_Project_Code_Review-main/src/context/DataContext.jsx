import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { api } from '../api/client'
import { useAuth } from './AuthContext'
import { setLiveUsers, setLiveProjects } from '../data/mockData'

const DataContext = createContext(null)

export function DataProvider({ children }) {
  const { currentUser } = useAuth()
  const [findings, setFindings] = useState([])
  const [projects, setProjects] = useState([])
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(false)

  const refreshData = useCallback(async () => {
    if (!currentUser) return
    setLoading(true)
    try {
      // 1. Fetch Users
      let fetchedUsers = []
      try {
        const userRes = await api.getUsers()
        fetchedUsers = (userRes || []).map((u) => ({
          ...u,
          userId: u.id,
          initials: (u.name || 'User').split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase(),
          color: '#7c3aed',
        }))
      } catch (err) {
        fetchedUsers = [{
          ...currentUser,
          userId: currentUser.id,
          initials: (currentUser.name || 'User').split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase(),
          color: '#7c3aed',
        }]
      }
      setUsers(fetchedUsers)
      setLiveUsers(fetchedUsers)

      // 2. Fetch Projects
      const projectList = await api.getProjects().catch(() => [])
      const enrichedProjects = await Promise.all(
        projectList.map(async (p) => {
          let members = []
          let repositories = []
          try {
            const m = await api.getProjectMembers(p.id)
            members = (m || []).map((mem) => mem.user_id || mem.id || mem)
          } catch (e) {
            members = [p.project_lead_id]
          }
          try {
            const r = await api.getProjectRepositories(p.id)
            repositories = (r || []).map((repo) => ({
              id: repo.id,
              name: repo.name,
              branch: repo.branch_name,
            }))
          } catch (e) {
            repositories = []
          }
          return {
            id: p.id,
            name: p.name,
            description: p.description || '',
            status: 'Active',
            lead: p.project_lead_id,
            project_lead_id: p.project_lead_id,
            members,
            repositories,
            created_at: p.created_at,
          }
        })
      )
      setProjects(enrichedProjects)
      setLiveProjects(enrichedProjects)

      // 3. Fetch Findings
      const findingRes = await api.getFindings({ page_size: 100 }).catch(() => ({ items: [] }))
      const rawFindings = findingRes?.items || (Array.isArray(findingRes) ? findingRes : [])
      const mappedFindings = await Promise.all(
        rawFindings.map(async (f) => {
          let history = []
          try {
            const statusHist = await api.getStatusHistory(f.id)
            history = (statusHist || []).map((h) => ({
              from: h.old_status,
              to: h.new_status,
              by: fetchedUsers.find((u) => u.id === h.changed_by)?.name || 'Admin',
              date: h.changed_at ? h.changed_at.slice(0, 10) : '',
              updatedAt: h.changed_at ? h.changed_at.slice(0, 10) : '',
              feedback: h.reason || '',
            }))
          } catch (e) {
            history = []
          }

          let attachments = []
          try {
            const atts = await api.getAttachments(f.id)
            attachments = (atts || []).map((a) => ({
              id: a.id,
              name: a.original_filename,
              type: a.media_type,
              size: a.size_bytes,
              kind: a.attachment_kind,
              dataUrl: api.getAttachmentDownloadUrl(a.id),
            }))
          } catch (e) {
            attachments = []
          }

          const acceptedEvent = history.find((event) => event.to === 'In Progress' && event.from === 'Open')

          return {
            id: f.id,
            code: f.finding_code,
            finding_code: f.finding_code,
            displayId: f.finding_code || f.id,
            title: f.title,
            description: f.description,
            project: f.project_id,
            project_id: f.project_id,
            repository: f.repository_id,
            repository_id: f.repository_id,
            severity: f.severity,
            status: f.status,
            label: f.category,
            category: f.category,
            assignee: f.assignee_id,
            assignee_id: f.assignee_id,
            reviewer: f.reviewer_id,
            reviewer_id: f.reviewer_id,
            dueDate: f.due_date,
            due_date: f.due_date,
            created: f.created_at ? f.created_at.slice(0, 10) : '',
            acceptedDate: acceptedEvent?.date || null,
            history,
            statusHistory: history,
            attachments,
          }
        })
      )
      setFindings(mappedFindings)
    } finally {
      setLoading(false)
    }
  }, [currentUser])

  useEffect(() => {
    refreshData()
  }, [refreshData])

  async function addFinding(findingData) {
    const projId = findingData.project || findingData.project_id
    const selectedProj = projects.find((p) => p.id === projId)

    // Resolve repository ID (must be a valid UUID for backend)
    let repository_id = findingData.repository || findingData.repository_id
    if (selectedProj?.repositories?.length) {
      const match = selectedProj.repositories.find((r) => r.id === repository_id || r.name === repository_id)
      if (match?.id) {
        repository_id = match.id
      }
    }

    // Resolve assignee ID (must be a valid UUID for backend)
    let assignee_id = findingData.assignee || findingData.assignee_id
    if (!assignee_id && selectedProj?.project_lead_id) {
      assignee_id = selectedProj.project_lead_id
    }
    if (!assignee_id && currentUser?.id) {
      assignee_id = currentUser.id
    }

    const payload = {
      title: findingData.title.trim(),
      description: findingData.description.trim(),
      category: findingData.label || findingData.category,
      project_id: projId,
      repository_id,
      severity: findingData.severity,
      due_date: findingData.dueDate || findingData.due_date,
      assignee_id,
    }
    const created = await api.createFinding(payload)
    if (findingData.attachments?.length) {
      for (const att of findingData.attachments) {
        const fileObj = att.file instanceof File ? att.file : (att instanceof File ? att : null)
        if (fileObj) {
          try {
            await api.uploadAttachment(created.id, fileObj, 'supporting_evidence')
          } catch (e) {
            console.error('Attachment upload failed:', e)
          }
        }
      }
    }
    await refreshData()
    return created
  }

  async function updateFindingStatus(id, newStatus, actorName, feedback = '', attachments = [], actorRole = 'user') {
    if (newStatus === 'In Review') {
      await api.submitForReview(id, feedback || 'Ready for review')
    } else {
      await api.updateFindingStatus(id, newStatus, feedback || null)
    }
    if (attachments && attachments.length > 0) {
      for (const att of attachments) {
        if (att.file instanceof File) {
          await api.uploadAttachment(id, att.file, 'resolution_proof')
        }
      }
    }
    await refreshData()
    return true
  }

  async function addProject(projectData) {
    const created = await api.createProject({
      name: projectData.name.trim(),
      description: (projectData.description || '').trim(),
    })
    // Add repositories
    if (projectData.repositories?.length) {
      for (const r of projectData.repositories) {
        const repoName = typeof r === 'string' ? r.trim() : r.name?.trim()
        if (repoName) {
          await api.addProjectRepository(created.id, { name: repoName })
        }
      }
    }
    // Add members
    if (projectData.members?.length) {
      for (const memberId of projectData.members) {
        if (memberId !== created.project_lead_id) {
          try {
            await api.addProjectMember(created.id, memberId)
          } catch (e) {
            // Already enrolled or lead
          }
        }
      }
    }
    await refreshData()
    return created
  }

  return (
    <DataContext.Provider
      value={{
        findings,
        projects,
        users,
        loading,
        refreshData,
        addFinding,
        updateFindingStatus,
        addProject,
      }}
    >
      {children}
    </DataContext.Provider>
  )
}

export function useData() {
  return useContext(DataContext)
}
