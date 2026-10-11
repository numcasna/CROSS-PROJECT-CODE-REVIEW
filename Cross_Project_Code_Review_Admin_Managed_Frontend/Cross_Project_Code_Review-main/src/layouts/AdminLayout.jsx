import { Outlet } from 'react-router-dom'
import Sidebar from '../components/Sidebar'

const items = [
  { to: '/admin/findings', label: 'Findings', icon: 'findings' },
  { to: '/admin/projects', label: 'Projects', icon: 'projects' },
]

export default function AdminLayout() {
  return <div className="app-shell"><Sidebar title="Dailoqua CPCRS" subtitle="Admin Workspace" items={items} /><main className="app-main"><Outlet /></main></div>
}
