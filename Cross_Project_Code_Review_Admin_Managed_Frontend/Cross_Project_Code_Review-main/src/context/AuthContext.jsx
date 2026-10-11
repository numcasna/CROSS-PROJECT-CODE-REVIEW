import { createContext, useContext, useState, useEffect } from 'react'
import { api } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('cpcrs_token')
    if (token) {
      api.getMe()
        .then((user) => {
          const role = user.role === 'developer' ? 'user' : user.role
          setCurrentUser({
            ...user,
            userId: user.id,
            role,
            backendRole: user.role,
          })
        })
        .catch(() => {
          localStorage.removeItem('cpcrs_token')
          setCurrentUser(null)
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  async function login({ email, password }) {
    const data = await api.login(email, password)
    const user = data.user
    const role = user.role === 'developer' ? 'user' : user.role
    const mapped = {
      ...user,
      userId: user.id,
      role,
      backendRole: user.role,
    }
    setCurrentUser(mapped)
    return mapped
  }

  async function logout() {
    await api.logout()
    setCurrentUser(null)
  }

  return (
    <AuthContext.Provider value={{ currentUser, loading, login, logout }}>
      {!loading && children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
