import { useState, useEffect } from 'react'
import { Card, Row, Col, Statistic, Button, Typography, Space, List, Avatar } from 'antd'
import {
  DatabaseOutlined,
  CloudUploadOutlined,
  LineChartOutlined,
  TeamOutlined,
  BellOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'

const { Title, Text, Paragraph } = Typography

interface RecentDataset {
  id: string
  name: string
  file_type: string
  created_at: string
}

export default function Dashboard() {
  const navigate = useNavigate()
  const [datasets, setDatasets] = useState<RecentDataset[]>([])

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await axios.get('/api/v1/datasets', {
        headers: { Authorization: `Bearer ${token}` },
        params: { limit: 5 },
      })
      setDatasets(response.data.items || [])
    } catch {
      setDatasets([])
    }
  }

  const quickActions = [
    {
      title: 'Upload Dataset',
      description: 'CSV, Excel, or JSON files',
      icon: <CloudUploadOutlined />,
      action: () => navigate('/datasets'),
      color: '#1677ff',
    },
    {
      title: 'Browse Datasets',
      description: 'View and manage your data',
      icon: <DatabaseOutlined />,
      action: () => navigate('/datasets'),
      color: '#52c41a',
    },
    {
      title: 'View Charts',
      description: 'Generated visualizations',
      icon: <LineChartOutlined />,
      action: () => navigate('/charts'),
      color: '#722ed1',
    },
    {
      title: 'Manage Teams',
      description: 'Collaborate with others',
      icon: <TeamOutlined />,
      action: () => navigate('/teams'),
      color: '#fa8c16',
    },
  ]

  const tips = [
    "Try asking: 'Show me the distribution of values'",
    'You can upload datasets up to 100MB',
    'Charts are automatically saved to your gallery',
    'Share datasets with your team for collaboration',
  ]

  return (
    <div>
      <Title level={3}>Dashboard</Title>

      {/* Stats Cards */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Datasets"
              value={datasets.length}
              prefix={<DatabaseOutlined />}
              valueStyle={{ color: '#1677ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Conversations"
              value={0}
              prefix={<LineChartOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Charts"
              value={0}
              prefix={<LineChartOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Teams"
              value={0}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        {/* Quick Actions */}
        <Col xs={24} lg={16}>
          <Card title="Quick Actions">
            <Row gutter={[16, 16]}>
              {quickActions.map((action, index) => (
                <Col xs={24} sm={12} key={index}>
                  <Card
                    size="small"
                    hoverable
                    onClick={action.action}
                    style={{ borderColor: action.color }}
                  >
                    <Space>
                      <div
                        style={{
                          width: 48,
                          height: 48,
                          borderRadius: 8,
                          background: `${action.color}15`,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: 24,
                          color: action.color,
                        }}
                      >
                        {action.icon}
                      </div>
                      <div>
                        <Text strong>{action.title}</Text>
                        <br />
                        <Text type="secondary" style={{ fontSize: 12 }}>{action.description}</Text>
                      </div>
                    </Space>
                  </Card>
                </Col>
              ))}
            </Row>
          </Card>

          {/* Recent Datasets */}
          <Card title="Recent Datasets" style={{ marginTop: 16 }}>
            {datasets.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px 0' }}>
                <DatabaseOutlined style={{ fontSize: 48, color: '#d9d9d9' }} />
                <Paragraph type="secondary" style={{ marginTop: 16 }}>
                  No datasets yet. Upload your first dataset to get started.
                </Paragraph>
                <Button type="primary" onClick={() => navigate('/datasets')}>
                  Upload Dataset
                </Button>
              </div>
            ) : (
              <List
                dataSource={datasets}
                renderItem={(item) => (
                  <List.Item
                    actions={[
                      <Button
                        type="link"
                        onClick={() => navigate(`/datasets/detail/${item.id}`)}
                      >
                        View
                      </Button>,
                      <Button
                        type="primary"
                        onClick={() => navigate(`/datasets/${item.id}`)}
                      >
                        Analyze
                      </Button>,
                    ]}
                  >
                    <List.Item.Meta
                      avatar={
                        <Avatar
                          style={{ backgroundColor: '#1677ff' }}
                          icon={<DatabaseOutlined />}
                        />
                      }
                      title={item.name}
                      description={`${item.file_type?.toUpperCase()} • ${new Date(item.created_at).toLocaleDateString()}`}
                    />
                  </List.Item>
                )}
              />
            )}
          </Card>
        </Col>

        {/* Sidebar */}
        <Col xs={24} lg={8}>
          {/* Tips */}
          <Card title="Getting Started">
            <List
              size="small"
              dataSource={tips}
              renderItem={(item, index) => (
                <List.Item>
                  <Space>
                    <Avatar
                      size="small"
                      style={{ backgroundColor: '#1677ff' }}
                    >
                      {index + 1}
                    </Avatar>
                    <Text>{item}</Text>
                  </Space>
                </List.Item>
              )}
            />
          </Card>

          {/* Shortcuts */}
          <Card title="Shortcuts" style={{ marginTop: 16 }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Button
                block
                style={{ textAlign: 'left', padding: '12px 16px' }}
                onClick={() => navigate('/profile')}
              >
                <Avatar size="small" style={{ marginRight: 8 }}>👤</Avatar>
                Edit Profile
              </Button>
              <Button
                block
                style={{ textAlign: 'left', padding: '12px 16px' }}
                onClick={() => navigate('/settings')}
              >
                <Avatar size="small" style={{ marginRight: 8 }}>⚙️</Avatar>
                Settings
              </Button>
              <Button
                block
                style={{ textAlign: 'left', padding: '12px 16px' }}
                onClick={() => navigate('/charts')}
              >
                <Avatar size="small" style={{ marginRight: 8 }}>📊</Avatar>
                View Charts
              </Button>
            </Space>
          </Card>

          {/* Notifications placeholder */}
          <Card title="Recent Activity" style={{ marginTop: 16 }}>
            <div style={{ textAlign: 'center', padding: '20px 0' }}>
              <BellOutlined style={{ fontSize: 32, color: '#d9d9d9' }} />
              <Paragraph type="secondary" style={{ marginTop: 8, marginBottom: 0 }}>
                No new notifications
              </Paragraph>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  )
}
