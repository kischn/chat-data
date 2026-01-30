import { useState } from 'react'
import {
  Card,
  Typography,
  Form,
  Input,
  Button,
  Switch,
  Select,
  Divider,
  message,
  Row,
  Col,
  Alert,
  Tabs,
  Space,
} from 'antd'
import {
  LockOutlined,
  BellOutlined,
  SafetyOutlined,
  GlobalOutlined,
} from '@ant-design/icons'

const { Title, Text, Paragraph } = Typography
const { TabPane } = Tabs

export default function Settings() {
  const [passwordForm] = Form.useForm()
  const [preferencesForm] = Form.useForm()
  const [saving, setSaving] = useState(false)

  const handlePasswordChange = async (values: {
    current_password: string
    new_password: string
    confirm_password: string
  }) => {
    if (values.new_password !== values.confirm_password) {
      message.error('Passwords do not match')
      return
    }

    setSaving(true)
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      message.success('Password changed successfully')
      passwordForm.resetFields()
    } catch (error) {
      message.error('Failed to change password')
    } finally {
      setSaving(false)
    }
  }

  const handlePreferencesSave = async (values: any) => {
    try {
      // Save to localStorage for now
      localStorage.setItem('preferences', JSON.stringify(values))
      message.success('Preferences saved')
    } catch (error) {
      message.error('Failed to save preferences')
    }
  }

  return (
    <div>
      <Title level={3}>Settings</Title>

      <Tabs defaultActiveKey="security" tabPosition="left">
        {/* Security Tab */}
        <TabPane
          tab={<span><SafetyOutlined /> Security</span>}
          key="security"
        >
          <Card title="Change Password">
            <Alert
              message="Password Requirements"
              description={
                <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
                  <li>At least 8 characters long</li>
                  <li>Contains uppercase and lowercase letters</li>
                  <li>Contains numbers and special characters</li>
                </ul>
              }
              type="info"
              showIcon
              style={{ marginBottom: 24 }}
            />

            <Form
              form={passwordForm}
              layout="vertical"
              onFinish={handlePasswordChange}
            >
              <Form.Item
                name="current_password"
                label="Current Password"
                rules={[{ required: true, message: 'Please enter current password' }]}
              >
                <Input.Password
                  prefix={<LockOutlined />}
                  placeholder="Enter current password"
                  size="large"
                />
              </Form.Item>

              <Form.Item
                name="new_password"
                label="New Password"
                rules={[
                  { required: true, message: 'Please enter new password' },
                  { min: 8, message: 'Password must be at least 8 characters' },
                ]}
              >
                <Input.Password
                  prefix={<LockOutlined />}
                  placeholder="Enter new password"
                  size="large"
                />
              </Form.Item>

              <Form.Item
                name="confirm_password"
                label="Confirm New Password"
                rules={[{ required: true, message: 'Please confirm password' }]}
              >
                <Input.Password
                  prefix={<LockOutlined />}
                  placeholder="Confirm new password"
                  size="large"
                />
              </Form.Item>

              <Form.Item style={{ marginBottom: 0 }}>
                <Button
                  type="primary"
                  htmlType="submit"
                  icon={<LockOutlined />}
                  loading={saving}
                  size="large"
                >
                  Change Password
                </Button>
              </Form.Item>
            </Form>
          </Card>

          <Card title="Two-Factor Authentication" style={{ marginTop: 16 }}>
            <Row justify="space-between" align="middle">
              <Col>
                <Text strong>Enable 2FA</Text>
                <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                  Add an extra layer of security to your account
                </Paragraph>
              </Col>
              <Col>
                <Switch />
              </Col>
            </Row>
          </Card>

          <Card title="Active Sessions" style={{ marginTop: 16 }}>
            <Alert
              message="Session Management"
              description="You are currently logged in on this device. You can sign out from other devices."
              type="warning"
              showIcon
              action={
                <Button danger size="small">
                  Sign Out All Other Devices
                </Button>
              }
            />
          </Card>
        </TabPane>

        {/* Notifications Tab */}
        <TabPane
          tab={<span><BellOutlined /> Notifications</span>}
          key="notifications"
        >
          <Card title="Email Notifications">
            <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
              <Col>
                <Text strong>Analysis Complete</Text>
                <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                  Receive notifications when AI analysis is complete
                </Paragraph>
              </Col>
              <Col>
                <Switch defaultChecked />
              </Col>
            </Row>

            <Divider style={{ margin: '16px 0' }} />

            <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
              <Col>
                <Text strong>New Team Members</Text>
                <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                  Get notified when someone joins your team
                </Paragraph>
              </Col>
              <Col>
                <Switch defaultChecked />
              </Col>
            </Row>

            <Divider style={{ margin: '16px 0' }} />

            <Row justify="space-between" align="middle">
              <Col>
                <Text strong>Weekly Digest</Text>
                <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                  Receive a weekly summary of your data activities
                </Paragraph>
              </Col>
              <Col>
                <Switch />
              </Col>
            </Row>
          </Card>
        </TabPane>

        {/* Preferences Tab */}
        <TabPane
          tab={<span><GlobalOutlined /> Preferences</span>}
          key="preferences"
        >
          <Card title="Display Preferences">
            <Form
              form={preferencesForm}
              layout="vertical"
              onFinish={handlePreferencesSave}
            >
              <Form.Item
                name="language"
                label="Language"
                initialValue="en"
              >
                <Select size="large" style={{ width: 200 }}>
                  <Select.Option value="en">English</Select.Option>
                  <Select.Option value="zh">中文</Select.Option>
                  <Select.Option value="es">Español</Select.Option>
                </Select>
              </Form.Item>

              <Form.Item
                name="timezone"
                label="Timezone"
                initialValue="UTC"
              >
                <Select size="large" style={{ width: 300 }}>
                  <Select.Option value="UTC">UTC (Coordinated Universal Time)</Select.Option>
                  <Select.Option value="America/New_York">Eastern Time (ET)</Select.Option>
                  <Select.Option value="America/Los_Angeles">Pacific Time (PT)</Select.Option>
                  <Select.Option value="Europe/London">London (GMT)</Select.Option>
                  <Select.Option value="Europe/Paris">Paris (CET)</Select.Option>
                  <Select.Option value="Asia/Shanghai">China (CST)</Select.Option>
                  <Select.Option value="Asia/Tokyo">Tokyo (JST)</Select.Option>
                </Select>
              </Form.Item>

              <Form.Item
                name="date_format"
                label="Date Format"
                initialValue="YYYY-MM-DD"
              >
                <Select size="large" style={{ width: 200 }}>
                  <Select.Option value="YYYY-MM-DD">YYYY-MM-DD</Select.Option>
                  <Select.Option value="MM/DD/YYYY">MM/DD/YYYY</Select.Option>
                  <Select.Option value="DD/MM/YYYY">DD/MM/YYYY</Select.Option>
                </Select>
              </Form.Item>

              <Form.Item style={{ marginBottom: 0, marginTop: 16 }}>
                <Space>
                  <Button type="primary" htmlType="submit" size="large">
                    Save Preferences
                  </Button>
                  <Button size="large">Reset to Default</Button>
                </Space>
              </Form.Item>
            </Form>
          </Card>

          <Card title="Theme" style={{ marginTop: 16 }}>
            <Row gutter={16}>
              <Col span={8}>
                <div
                  style={{
                    height: 100,
                    background: '#1677ff',
                    borderRadius: 8,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                    fontWeight: 'bold',
                    cursor: 'pointer',
                    border: '2px solid #1677ff',
                  }}
                >
                  Light
                </div>
              </Col>
              <Col span={8}>
                <div
                  style={{
                    height: 100,
                    background: '#141414',
                    borderRadius: 8,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                    fontWeight: 'bold',
                    cursor: 'pointer',
                    border: '1px solid #303030',
                  }}
                >
                  Dark
                </div>
              </Col>
              <Col span={8}>
                <div
                  style={{
                    height: 100,
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    borderRadius: 8,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                    fontWeight: 'bold',
                    cursor: 'pointer',
                    border: '1px solid #ddd',
                  }}
                >
                  System
                </div>
              </Col>
            </Row>
          </Card>
        </TabPane>

        {/* Data Tab */}
        <TabPane
          tab={<span><SafetyOutlined /> Data & Privacy</span>}
          key="data"
        >
          <Card title="Export Your Data">
            <Paragraph>
              Download a copy of all your data including datasets, conversations, and settings.
            </Paragraph>
            <Button size="large">Export All Data</Button>
          </Card>

          <Card title="Delete Account" style={{ marginTop: 16 }}>
            <Alert
              message="Danger Zone"
              description="Once you delete your account, there is no going back. Please be certain."
              type="error"
              showIcon
              style={{ marginBottom: 16 }}
              action={
                <Button danger size="small">
                  Delete Account
                </Button>
              }
            />
          </Card>
        </TabPane>
      </Tabs>
    </div>
  )
}
