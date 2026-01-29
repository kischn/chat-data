import { useState } from 'react'
import { Card, Form, Input, Button, Typography, Tabs, message } from 'antd'
import axios from 'axios'

const { Title, Text } = Typography

interface LoginProps {
  onLogin: (token: string) => void
}

export default function Login({ onLogin }: LoginProps) {
  const [loading, setLoading] = useState(false)

  const handleRegister = async (values: { email: string; username: string; password: string }) => {
    setLoading(true)
    try {
      await axios.post('/api/v1/auth/register', values)
      message.success('Registration successful! Please login.')
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  const handleLogin = async (values: { email: string; password: string }) => {
    setLoading(true)
    try {
      const response = await axios.post('/api/v1/auth/login', values)
      onLogin(response.data.access_token)
      message.success('Login successful!')
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: '#f0f2f5' }}>
      <Card style={{ width: 400 }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <Title level={2}>Chat Data</Title>
          <Text type="secondary">AI-powered Data Analysis Platform</Text>
        </div>

        <Tabs
          items={[
            {
              key: 'login',
              label: 'Login',
              children: (
                <Form onFinish={handleLogin} layout="vertical">
                  <Form.Item name="email" label="Email" rules={[{ required: true, type: 'email' }]}>
                    <Input placeholder="your@email.com" />
                  </Form.Item>
                  <Form.Item name="password" label="Password" rules={[{ required: true }]}>
                    <Input.Password placeholder="Enter password" />
                  </Form.Item>
                  <Button type="primary" htmlType="submit" loading={loading} block>
                    Login
                  </Button>
                </Form>
              ),
            },
            {
              key: 'register',
              label: 'Register',
              children: (
                <Form onFinish={handleRegister} layout="vertical">
                  <Form.Item name="email" label="Email" rules={[{ required: true, type: 'email' }]}>
                    <Input placeholder="your@email.com" />
                  </Form.Item>
                  <Form.Item name="username" label="Username" rules={[{ required: true }]}>
                    <Input placeholder="Choose a username" />
                  </Form.Item>
                  <Form.Item name="password" label="Password" rules={[{ required: true, min: 8 }]}>
                    <Input.Password placeholder="Min 8 characters" />
                  </Form.Item>
                  <Button type="primary" htmlType="submit" loading={loading} block>
                    Register
                  </Button>
                </Form>
              ),
            },
          ]}
        />
      </Card>
    </div>
  )
}
