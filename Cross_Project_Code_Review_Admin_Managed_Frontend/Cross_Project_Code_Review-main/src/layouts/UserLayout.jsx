import { Outlet } from 'react-router-dom'
import Sidebar from '../components/Sidebar'

const items = [
  { to: '/user/findings', label: 'My Findings', icon: 'findings' },
  { to: '/user/projects', label: 'Projects', icon: 'projects' },
]

export default function UserLayout() {
  return <div className="app-shell"><Sidebar title="Dailoqa CPCRS" subtitle="Developer Workspace" items={items} /><main className="app-main"><Outlet /></main></div>
}
