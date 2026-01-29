import { useState, useEffect } from 'react'
import {
  Card,
  Table,
  Button,
  Modal,
  Form,
  Input,
  Tag,
  message,
  Space,
  Popconfirm,
} from 'antd'
import { PlusOutlined, TeamOutlined, UserOutlined } from '@ant-design/icons'
import { teamApi } from '../api/client'

interface Team {
  id: string
  name: string
  created_at: string
}

interface Member {
  user_id: string
  role: string
  joined_at: string
  user?: {
    email: string
    username: string
  }
}

export default function Teams() {
  const [teams, setTeams] = useState<Team[]>([])
  const [loading, setLoading] = useState(false)
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [membersModalOpen, setMembersModalOpen] = useState(false)
  const [selectedTeam, setSelectedTeam] = useState<Team | null>(null)
  const [members, setMembers] = useState<Member[]>([])
  const [addMemberEmail, setAddMemberEmail] = useState('')
  const [form] = Form.useForm()

  useEffect(() => {
    fetchTeams()
  }, [])

  const fetchTeams = async () => {
    setLoading(true)
    try {
      const response = await teamApi.list()
      setTeams(response.data)
    } catch (error) {
      message.error('Failed to load teams')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateTeam = async (values: { name: string }) => {
    try {
      await teamApi.create(values)
      message.success('Team created successfully')
      setCreateModalOpen(false)
      form.resetFields()
      fetchTeams()
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Failed to create team')
    }
  }

  const handleViewMembers = async (team: Team) => {
    setSelectedTeam(team)
    setMembersModalOpen(true)
    try {
      const response = await teamApi.listMembers(team.id)
      setMembers(response.data)
    } catch (error) {
      message.error('Failed to load members')
    }
  }

  const handleAddMember = async () => {
    if (!selectedTeam || !addMemberEmail) return

    try {
      await teamApi.addMember(selectedTeam.id, addMemberEmail)
      message.success('Member added successfully')
      setAddMemberEmail('')
      const response = await teamApi.listMembers(selectedTeam.id)
      setMembers(response.data)
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Failed to add member')
    }
  }

  const handleRemoveMember = async (userId: string) => {
    if (!selectedTeam) return

    try {
      await teamApi.removeMember(selectedTeam.id, userId)
      message.success('Member removed successfully')
      const response = await teamApi.listMembers(selectedTeam.id)
      setMembers(response.data)
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Failed to remove member')
    }
  }

  const columns = [
    {
      title: 'Team Name',
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => (
        <Space>
          <TeamOutlined />
          {name}
        </Space>
      ),
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleDateString(),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: Team) => (
        <Space>
          <Button size="small" onClick={() => handleViewMembers(record)}>
            Members
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <h1>Teams</h1>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalOpen(true)}>
          Create Team
        </Button>
      </div>

      <Card>
        <Table
          dataSource={teams}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={false}
        />
      </Card>

      {/* Create Team Modal */}
      <Modal
        title="Create Team"
        open={createModalOpen}
        onCancel={() => setCreateModalOpen(false)}
        onOk={() => form.submit()}
      >
        <Form form={form} onFinish={handleCreateTeam} layout="vertical">
          <Form.Item
            name="name"
            label="Team Name"
            rules={[{ required: true, message: 'Please enter team name' }]}
          >
            <Input placeholder="Enter team name" />
          </Form.Item>
        </Form>
      </Modal>

      {/* Members Modal */}
      <Modal
        title={`Team Members - ${selectedTeam?.name}`}
        open={membersModalOpen}
        onCancel={() => setMembersModalOpen(false)}
        footer={null}
        width={600}
      >
        <div style={{ marginBottom: 16 }}>
          <Space>
            <Input
              placeholder="Add member by email"
              value={addMemberEmail}
              onChange={(e) => setAddMemberEmail(e.target.value)}
              style={{ width: 200 }}
            />
            <Button type="primary" onClick={handleAddMember}>
              Add
            </Button>
          </Space>
        </div>

        <Table
          dataSource={members}
          rowKey="user_id"
          pagination={false}
          columns={[
            {
              title: 'User',
              render: (_: any, record: Member) => (
                <Space>
                  <UserOutlined />
                  <span>{record.user?.username || record.user_id}</span>
                </Space>
              ),
            },
            {
              title: 'Email',
              render: (_: any, record: Member) => record.user?.email || '-',
            },
            {
              title: 'Role',
              dataIndex: 'role',
              render: (role: string) => (
                <Tag color={role === 'owner' ? 'gold' : role === 'admin' ? 'blue' : 'green'}>
                  {role}
                </Tag>
              ),
            },
            {
              title: 'Actions',
              render: (_: any, record: Member) =>
                record.role !== 'owner' ? (
                  <Popconfirm
                    title="Remove this member?"
                    onConfirm={() => handleRemoveMember(record.user_id)}
                  >
                    <Button size="small" danger>
                      Remove
                    </Button>
                  </Popconfirm>
                ) : null,
            },
          ]}
        />
      </Modal>
    </div>
  )
}
