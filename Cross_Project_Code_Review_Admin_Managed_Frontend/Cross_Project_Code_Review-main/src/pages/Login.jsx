import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Icon from '../components/Icon'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  async function submit(e) {
    e.preventDefault()
    if (!email.trim() || !password) {
      setError('Please enter both email and password.')
      return
    }
    setError('')
    setSubmitting(true)
    try {
      const user = await login({ email: email.trim(), password })
      navigate(user.role === 'admin' ? '/admin' : '/user')
    } catch (err) {
      setError(err.message || 'Login failed. Please check your credentials.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="login-shell">
      <div className="login-panel">
        <div className="login-mark">
          <Icon name="findings" size={22} />
        </div>
        <p className="eyebrow">DAILOQUA · CROSS PROJECT CODE REVIEW</p>
        <h1>Code review findings, in one workspace.</h1>
        <p className="login-copy">
          Dailoqua Engineering Portal — Track findings, projects, resolver decisions, and remediation progress across engineering teams.
        </p>

        <form onSubmit={submit} className="login-form">
          <label>
            Email Address
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="e.g. admin@cpcrs.com or alice@cpcrs.com"
              autoComplete="email"
              required
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
              autoComplete="current-password"
              required
            />
          </label>
          {error && <p className="form-error">{error}</p>}
          <button className="btn btn-primary login-button" type="submit" disabled={submitting}>
            {submitting ? 'Signing in...' : 'Log in'}
          </button>
        </form>

        <div style={{ marginTop: '1.5rem', paddingTop: '1rem', borderTop: '1px solid #e2e8f0', textAlign: 'center', fontSize: '0.8rem', color: '#64748b' }}>
          Developed for <strong>Dailoqua</strong> by the Engineering Intern Team
        </div>
      </div>
    </div>
  )
}
