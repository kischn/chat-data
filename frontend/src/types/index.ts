// User types
export interface User {
  id: string
  email: string
  username: string
  is_active: boolean
  created_at: string
}

export interface UserUpdate {
  username?: string
  email?: string
}

export interface PasswordChange {
  current_password: string
  new_password: string
}

// Dataset types
export interface Dataset {
  id: string
  name: string
  description: string | null
  file_type: string | null
  file_size: number | null
  file_path: string
  owner_id: string
  team_id: string | null
  is_public: boolean
  metadata: DatasetMetadata | null
  columns: DatasetColumn[]
  created_at: string
  updated_at: string
}

export interface DatasetMetadata {
  row_count?: number
  column_count?: number
  columns?: Record<string, ColumnStatistics>
}

export interface DatasetColumn {
  id: string
  name: string
  data_type: string | null
  nullable: boolean
  statistics: ColumnStatistics | null
  sample_values: any[] | null
  position: number
}

export interface ColumnStatistics {
  dtype: string
  null_rate: number
  mean?: number
  std?: number
  min?: number
  max?: number
  unique_count?: number
}

// Conversation types
export interface Conversation {
  id: string
  dataset_id: string
  title: string
  created_at: string
  updated_at: string
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  code_result?: CodeResult
  created_at: string
}

export interface CodeResult {
  output: string
  charts?: ChartInfo[]
  error?: string
}

export interface ChartInfo {
  id: string
  type: string
  url?: string
}

// Team types
export interface Team {
  id: string
  name: string
  created_at: string
}

export interface TeamMember {
  user_id: string
  email: string
  username: string
  role: string
  joined_at: string
}

// Chart types
export interface Chart {
  id: string
  chart_type: string
  dataset_id: string
  created_at: string
}

export interface ChartSuggestion {
  type: string
  description: string
  columns: Record<string, string>
}

// API Response types
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  skip: number
  limit: number
}

// Cleaning types
export interface CleaningSuggestion {
  type: string
  column: string
  rate: number | null
  count: number | null
  strategy: string
  reason: string
}

export interface CleaningOperation {
  type: string
  column: string
  strategy: string
}

export interface CleaningResult {
  new_dataset_id: string
  new_dataset_name: string
  original_shape: number[]
  cleaned_shape: number[]
  operations_applied: Record<string, any>[]
}
