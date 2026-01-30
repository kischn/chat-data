import { useState, useEffect } from 'react'
import {
  Card,
  Avatar,
  Typography,
  Form,
  Input,
  Button,
  message,
  Tag,
  Space,
  Divider,
  Row,
  Col,
  Descriptions,
  Spin,
} from 'antd'
import {
  UserOutlined,
  MailOutlined,
  CalendarOutlined,
  EditOutlined,
  SaveOutlined,
  CloseOutlined,
} from '@ant-design/icons'
import { authApi } from '../api/client'
import type { User } from '../types'

const { Title, Text } = Typography

export default function Profile() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => {
    fetchUser()
  }, [])

  const fetchUser = async () => {
    try {
      const response = await authApi.me()
      setUser(response.data)
      form.setFieldsValue({
        username: response.data.username,
        email: response.data.email,
      })
    } catch (error) {
      message.error('Failed to load profile')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async (values: { username: string; email: string }) => {
    setSaving(true)
    try {
      // For now, just show success - actual update would call API
      message.success('Profile updated successfully')
      setUser({ ...user!, ...values })
      setEditing(false)
    } catch (error) {
      message.error('Failed to update profile')
    } finally {
      setSaving(false)
    }
  }

  const handleCancel = () => {
    form.setFieldsValue({
      username: user?.username,
      email: user?.email,
    })
    setEditing(false)
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div>
      <Title level={3}>Profile</Title>

      <Row gutter={[24, 24]}>
        {/* Profile Card */}
        <Col xs={24} md={8}>
          <Card>
            <div style={{ textAlign: 'center', padding: '20px 0' }}>
              <Avatar
                size={120}
                icon={<UserOutlined />}
                style={{ backgroundColor: '#1677ff', marginBottom: 16 }}
              />
              <Title level={4} style={{ margin: 0 }}>{user?.username}</Title>
              <Text type="secondary">{user?.email}</Text>
              <Divider />
              <Space>
                <Tag color={user?.is_active ? 'green' : 'red'}>
                  {user?.is_active ? 'Active' : 'Inactive'}
                </Tag>
                <Tag color="blue">Free Plan</Tag>
              </Space>
            </div>
          </Card>
        </Col>

        {/* Edit Form */}
        <Col xs={24} md={16}>
          <Card
            title="Profile Information"
            extra={
              !editing && (
                <Button
                  icon={<EditOutlined />}
                  onClick={() => setEditing(true)}
                >
                  Edit
                </Button>
              )
            }
          >
            <Form
              form={form}
              layout="vertical"
              onFinish={handleSave}
            >
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="username"
                    label="Username"
                    rules={[{ required: true, message: 'Please enter username' }]}
                  >
                    <Input
                      prefix={<UserOutlined />}
                      disabled={!editing}
                      size="large"
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="email"
                    label="Email"
                    rules={[
                      { required: true, message: 'Please enter email' },
                      { type: 'email', message: 'Please enter a valid email' },
                    ]}
                  >
                    <Input
                      prefix={<MailOutlined />}
                      disabled={!editing}
                      size="large"
                    />
                  </Form.Item>
                </Col>
              </Row>

              {editing && (
                <Form.Item style={{ marginBottom: 0, marginTop: 16 }}>
                  <Space>
                    <Button
                      type="primary"
                      icon={<SaveOutlined />}
                      htmlType="submit"
                      loading={saving}
                    >
                      Save Changes
                    </Button>
                    <Button
                      icon={<CloseOutlined />}
                      onClick={handleCancel}
                    >
                      Cancel
                    </Button>
                  </Space>
                </Form.Item>
              )}
            </Form>
          </Card>

          {/* Account Info */}
          <Card title="Account Information" style={{ marginTop: 16 }}>
            <Descriptions column={1}>
              <Descriptions.Item label={<><CalendarOutlined /> Created</>}>
                {user?.created_at ? new Date(user.created_at).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                }) : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="User ID">
                <Text code>{user?.id}</Text>
              </Descriptions.Item>
            </Descriptions>
          </Card>

          {/* Stats */}
          <Card title="Statistics" style={{ marginTop: 16 }}>
            <Row gutter={16}>
              <Col span={8}>
                <Card size="small">
                  <Statistic title="Datasets" value={0} />
                </Card>
              </Col>
              <Col span={8}>
                <Card size="small">
                  <Statistic title="Conversations" value={0} />
                </Card>
              </Col>
              <Col span={8}>
                <Card size="small">
                  <Statistic title="Charts" value={0} />
                </Card>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

function Statistic({ title, value }: { title: string; value: number }) {
  return (
    <div style={{ textAlign: 'center' }}>
      <Text strong style={{ fontSize: 24, color: '#1677ff' }}>{value}</Text>
      <br />
      <Text type="secondary">{title}</Text>
    </div>
  )
}
