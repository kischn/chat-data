import { Routes, Route, Navigate } from 'react-router-dom'
import { useState } from 'react'
import { Layout, Menu } from 'antd'
import { DashboardOutlined, DatasetOutlined, TeamOutlined, LineChartOutlined } from '@ant-design/icons'
import { useNavigate, useLocation } from 'react-router-dom'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import DatasetList from './pages/DatasetList'
import Analysis from './pages/Analysis'
import Teams from './pages/Teams'

const { Header, Content, Sider } = Layout

function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'))
  const navigate = useNavigate()
  const location = useLocation()

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

  const menuItems = [
    { key: '/', icon: <DashboardOutlined />, label: 'Dashboard' },
    { key: '/datasets', icon: <DatasetOutlined />, label: 'Datasets' },
    { key: '/teams', icon: <TeamOutlined />, label: 'Teams' },
  ]

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible theme="dark">
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontSize: '1.1rem',
            fontWeight: 'bold',
          }}
        >
          Chat Data
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            padding: '0 24px',
            background: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: '0 1px 4px rgba(0,0,0,0.1)',
          }}
        >
          <div style={{ fontSize: '1.2rem', fontWeight: 500 }}>
            {location.pathname === '/' && 'Dashboard'}
            {location.pathname === '/datasets' && 'Datasets'}
            {location.pathname.startsWith('/datasets/') && 'Analysis'}
            {location.pathname === '/teams' && 'Teams'}
          </div>
          <a
            onClick={handleLogout}
            style={{ color: '#666', cursor: 'pointer' }}
          >
            Logout
          </a>
        </Header>
        <Content style={{ margin: 24, padding: 24, background: '#fff', borderRadius: 8 }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/datasets" element={<DatasetList />} />
            <Route path="/datasets/:id" element={<Analysis />} />
            <Route path="/teams" element={<Teams />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  )
}

export default App
