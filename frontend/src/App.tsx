import { Routes, Route, Navigate } from 'react-router-dom'
import { useState } from 'react'
import { Layout } from 'antd'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import DatasetList from './pages/DatasetList'
import Analysis from './pages/Analysis'

const { Header, Content } = Layout

function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'))

  const handleLogin = (newToken: string) => {
    localStorage.setItem('token', newToken)
    setToken(newToken)
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    setToken(null)
  }

  if (!token) {
    return <Login onLogin={handleLogin} />
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ color: 'white', fontSize: '1.2rem', fontWeight: 'bold' }}>
          Chat Data Platform
        </div>
        <a onClick={handleLogout} style={{ color: 'white', cursor: 'pointer' }}>
          Logout
        </a>
      </Header>
      <Content style={{ padding: '24px' }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/datasets" element={<DatasetList />} />
          <Route path="/datasets/:id" element={<Analysis />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Content>
    </Layout>
  )
}

export default App
