import { Routes, Route, Navigate } from 'react-router-dom'
import { useState } from 'react'
import { Layout, Menu, Avatar, Dropdown, Space } from 'antd'
import {
  DashboardOutlined,
  DatabaseOutlined,
  TeamOutlined,
  LineChartOutlined,
  UserOutlined,
  SettingOutlined,
  LogoutOutlined,
  ProfileOutlined,
} from '@ant-design/icons'
import { useNavigate, useLocation } from 'react-router-dom'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import DatasetList from './pages/DatasetList'
import DatasetDetail from './pages/DatasetDetail'
import Analysis from './pages/Analysis'
import Teams from './pages/Teams'
import Profile from './pages/Profile'
import Settings from './pages/Settings'
import ChartsGallery from './pages/ChartsGallery'

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

  const getPageTitle = () => {
    const path = location.pathname
    if (path === '/') return 'Dashboard'
    if (path === '/datasets') return 'Datasets'
    if (path.startsWith('/datasets/') && path.split('/').length > 2) {
      if (path.split('/')[2] === '') return 'Dataset Detail'
      return 'Analysis'
    }
    if (path === '/teams') return 'Teams'
    if (path === '/profile') return 'Profile'
    if (path === '/settings') return 'Settings'
    if (path === '/charts') return 'Charts Gallery'
    return 'Chat Data'
  }

  if (!token) {
    return <Login onLogin={handleLogin} />
  }

  const menuItems = [
    { key: '/', icon: <DashboardOutlined />, label: 'Dashboard' },
    { key: '/datasets', icon: <DatabaseOutlined />, label: 'Datasets' },
    { key: '/teams', icon: <TeamOutlined />, label: 'Teams' },
    { key: '/charts', icon: <LineChartOutlined />, label: 'Charts' },
  ]

  const userMenuItems = [
    {
      key: 'profile',
      icon: <ProfileOutlined />,
      label: 'Profile',
      onClick: () => navigate('/profile'),
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: 'Settings',
      onClick: () => navigate('/settings'),
    },
    { type: 'divider' as const },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Logout',
      danger: true,
      onClick: handleLogout,
    },
  ]

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible theme="dark" width={240}>
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontSize: '1.1rem',
            fontWeight: 'bold',
            borderBottom: '1px solid rgba(255,255,255,0.1)',
          }}
        >
          <LineChartOutlined style={{ marginRight: 8 }} />
          Chat Data
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ borderRight: 0 }}
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
            {getPageTitle()}
          </div>
          <Dropdown menu={{ items: userMenuItems }} trigger={['click']}>
            <Space style={{ cursor: 'pointer' }}>
              <Avatar icon={<UserOutlined />} style={{ backgroundColor: '#1677ff' }} />
              <span>User</span>
            </Space>
          </Dropdown>
        </Header>
        <Content style={{ margin: 24, padding: 24, background: '#f5f5f5', minHeight: 'calc(100vh - 112px)' }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/datasets" element={<DatasetList />} />
            <Route path="/datasets/:id" element={<Analysis />} />
            <Route path="/datasets/detail/:id" element={<DatasetDetail />} />
            <Route path="/teams" element={<Teams />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/charts" element={<ChartsGallery />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  )
}

export default App
