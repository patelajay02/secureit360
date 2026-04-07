'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

const ADMIN_PASSWORD = 'SecureIT360Admin2026!'

export default function AdminPage() {
  const router = useRouter()
  const [authenticated, setAuthenticated] = useState(false)
  const [password, setPassword] = useState('')
  const [passwordError, setPasswordError] = useState('')
  const [users, setUsers] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [deleting, setDeleting] = useState<string | null>(null)

  const handlePasswordSubmit = () => {
    if (password === ADMIN_PASSWORD) {
      setAuthenticated(true)
      fetchUsers()
    } else {
      setPasswordError('Incorrect password.')
    }
  }

  const fetchUsers = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/admin/users`)
      const data = await response.json()
      setUsers(data.users || [])
    } catch (err) {
      setMessage('Failed to load users.')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (userId: string, email: string) => {
    if (!confirm(`Are you sure you want to delete ${email}? This cannot be undone.`)) return

    setDeleting(userId)
    setMessage('')

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/admin/delete/${userId}`, {
        method: 'DELETE'
      })

      const data = await response.json()

      if (response.ok) {
        setMessage(`✅ ${email} deleted successfully.`)
        setUsers(users.filter(u => u.user_id !== userId))
      } else {
        setMessage(`❌ Failed to delete: ${data.detail}`)
      }
    } catch (err) {
      setMessage('❌ Something went wrong.')
    } finally {
      setDeleting(null)
    }
  }

  if (!authenticated) {
    return (
      <main className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
        <div className="w-full max-w-sm">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">
              SecureIT<span className="text-red-500">360</span>
            </h1>
            <p className="text-gray-400 text-sm">Admin Panel</p>
          </div>
          <div className="bg-gray-900 rounded-2xl p-8 border border-gray-800">
            <h2 className="text-white font-semibold mb-4">Enter admin password</h2>
            {passwordError && (
              <div className="bg-red-900/30 border border-red-700 text-red-300 rounded-lg p-3 mb-4 text-sm">
                {passwordError}
              </div>
            )}
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handlePasswordSubmit()}
              className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-3 focus:outline-none focus:border-red-500 mb-4"
            />
            <button
              onClick={handlePasswordSubmit}
              className="w-full bg-red-600 hover:bg-red-700 text-white font-semibold rounded-lg py-3 transition"
            >
              Enter
            </button>
          </div>
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-gray-950 text-white">
      <nav className="bg-gray-900 border-b border-gray-800 px-6 py-4 flex justify-between items-center">
        <h1 className="text-xl font-bold">
          SecureIT<span className="text-red-500">360</span>
          <span className="text-gray-500 text-sm font-normal ml-2">Admin Panel</span>
        </h1>
        <button
          onClick={() => router.push('/')}
          className="text-gray-400 hover:text-white text-sm"
        >
          Back to site
        </button>
      </nav>

      <div className="max-w-6xl mx-auto px-6 py-8">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold">Registered Companies</h2>
          <button
            onClick={fetchUsers}
            className="bg-gray-800 hover:bg-gray-700 text-white text-sm px-4 py-2 rounded-lg transition"
          >
            Refresh
          </button>
        </div>

        {message && (
          <div className={`rounded-lg p-3 mb-6 text-sm ${message.startsWith('✅') ? 'bg-green-900/30 border border-green-700 text-green-300' : 'bg-red-900/30 border border-red-700 text-red-300'}`}>
            {message}
          </div>
        )}

        {loading ? (
          <p className="text-gray-400">Loading users...</p>
        ) : users.length === 0 ? (
          <p className="text-gray-400">No users found.</p>
        ) : (
          <div className="bg-gray-900 rounded-2xl border border-gray-800 overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-800">
                  <th className="text-left text-gray-400 text-sm px-6 py-4">Company</th>
                  <th className="text-left text-gray-400 text-sm px-6 py-4">Email</th>
                  <th className="text-left text-gray-400 text-sm px-6 py-4">Country</th>
                  <th className="text-left text-gray-400 text-sm px-6 py-4">Status</th>
                  <th className="text-left text-gray-400 text-sm px-6 py-4">Joined</th>
                  <th className="text-left text-gray-400 text-sm px-6 py-4">Action</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user, index) => (
                  <tr key={index} className="border-b border-gray-800 last:border-0">
                    <td className="px-6 py-4 text-white text-sm">{user.company_name}</td>
                    <td className="px-6 py-4 text-gray-300 text-sm">{user.email}</td>
                    <td className="px-6 py-4 text-gray-300 text-sm">{user.country}</td>
                    <td className="px-6 py-4">
                      <span className={`text-xs px-2 py-1 rounded font-medium ${
                        user.status === 'trial' ? 'bg-amber-900/50 text-amber-300' :
                        user.status === 'active' ? 'bg-green-900/50 text-green-300' :
                        'bg-gray-700 text-gray-300'
                      }`}>
                        {user.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-gray-400 text-sm">
                      {new Date(user.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4">
                      <button
                        onClick={() => handleDelete(user.user_id, user.email)}
                        disabled={deleting === user.user_id}
                        className="bg-red-900/50 hover:bg-red-700 text-red-300 hover:text-white text-xs px-3 py-1.5 rounded transition disabled:opacity-50"
                      >
                        {deleting === user.user_id ? 'Deleting...' : 'Delete'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </main>
  )
}