import { useRef, useState } from 'react'
import Topbar from '../components/Topbar'
import Avatar from '../components/Avatar'
import Icon from '../components/Icon'
import { useAuth } from '../context/AuthContext'

export default function Settings() {
  const { currentUser, updateProfilePicture, changePassword } = useAuth()
  const inputRef = useRef(null)
  const [preview, setPreview] = useState(currentUser?.avatar || '')
  const [passwords, setPasswords] = useState({ current: '', next: '', confirm: '' })
  const [message, setMessage] = useState(null)

  function selectPicture(event) {
    const file = event.target.files?.[0]
    if (!file) return
    if (!file.type.startsWith('image/')) {
      setMessage({ type: 'error', text: 'Please select an image file.' })
      return
    }
    const reader = new FileReader()
    reader.onload = () => setPreview(reader.result)
    reader.readAsDataURL(file)
  }

  function savePicture() {
    if (!preview) {
      setMessage({ type: 'error', text: 'Choose an image first.' })
      return
    }
    updateProfilePicture(preview)
    setMessage({ type: 'success', text: 'Profile picture updated.' })
  }

  function handlePassword(e) {
    e.preventDefault()
    setMessage(null)
    if (!passwords.current || !passwords.next || !passwords.confirm) {
      setMessage({ type: 'error', text: 'All password fields are required.' })
      return
    }
    if (passwords.next !== passwords.confirm) {
      setMessage({ type: 'error', text: 'New password and confirmation must match.' })
      return
    }
    const result = changePassword(passwords.current, passwords.next)
    setMessage({ type: result.ok ? 'success' : 'error', text: result.message })
    if (result.ok) setPasswords({ current: '', next: '', confirm: '' })
  }

  return <div><Topbar title="Settings" /><div className="page-container settings-page">
    <section className="settings-card">
      <div className="section-heading"><div><h2>Profile</h2><p>Manage the profile information used across the workspace.</p></div></div>
      <div className="profile-editor">
        <div className="profile-preview"><Avatar user={{ ...currentUser, avatar: preview }} size={88} /></div>
        <div className="profile-actions"><strong>{currentUser?.name}</strong><span>{currentUser?.role === 'admin' ? 'Lead Reviewer' : 'Backend Engineer'}</span>
          <div className="button-row"><button className="btn btn-secondary" type="button" onClick={() => inputRef.current?.click()}><Icon name="upload" size={16}/> Choose picture</button><button className="btn btn-primary" type="button" onClick={savePicture}>Save picture</button></div>
          <input ref={inputRef} type="file" accept="image/*" onChange={selectPicture} className="sr-only" />
          <small>PNG, JPG or other standard image formats. Preview before saving.</small>
        </div>
      </div>
    </section>

    <section className="settings-card">
      <div className="section-heading"><div><h2>Change password</h2><p>Update your mock-auth password. Password values are never displayed.</p></div><Icon name="lock" size={20}/></div>
      <form onSubmit={handlePassword} className="form-grid password-grid">
        <label>Current Password<input type="password" autoComplete="current-password" value={passwords.current} onChange={(e) => setPasswords({...passwords, current:e.target.value})}/></label>
        <label>New Password<input type="password" autoComplete="new-password" value={passwords.next} onChange={(e) => setPasswords({...passwords, next:e.target.value})}/></label>
        <label>Confirm New Password<input type="password" autoComplete="new-password" value={passwords.confirm} onChange={(e) => setPasswords({...passwords, confirm:e.target.value})}/></label>
        <div className="form-actions"><button className="btn btn-primary" type="submit">Change Password</button></div>
      </form>
      </section>
    {message && <div className={`flash ${message.type}`}>{message.text}</div>}
  </div></div>
}
