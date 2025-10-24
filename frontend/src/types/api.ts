/**
 * TypeScript types generated from FastAPI backend
 *
 * These types match the Pydantic models in ignition_toolkit/api/app.py
 */

export interface ParameterInfo {
  name: string;
  type: string;
  required: boolean;
  default: string | null;
  description: string;
}

export interface StepInfo {
  id: string;
  name: string;
  type: string;
  timeout: number;
  retry_count: number;
}

export interface PlaybookInfo {
  name: string;
  path: string;
  version: string;
  description: string;
  parameter_count: number;
  step_count: number;
  parameters: ParameterInfo[];
  steps: StepInfo[];
  // Metadata fields
  revision: number;
  verified: boolean;
  enabled: boolean;
  last_modified: string | null;
  verified_at: string | null;
}

export interface ExecutionRequest {
  playbook_path: string;
  parameters: Record<string, string>;
  gateway_url?: string;
  credential_name?: string;
  debug_mode?: boolean;
}

export interface ExecutionResponse {
  execution_id: string;
  status: string;
  message: string;
}

export interface ExecutionStatusResponse {
  execution_id: string;
  playbook_name: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  current_step_index: number;
  total_steps: number;
  error: string | null;
  step_results?: StepResult[];
}

export interface CredentialInfo {
  name: string;
  username: string;
  gateway_url?: string;
  description?: string;
}

export interface CredentialCreate {
  name: string;
  username: string;
  password: string;
  gateway_url?: string;
  description?: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  timestamp: string;
}

// WebSocket message types
export interface StepResult {
  step_id: string;
  step_name: string;
  status: string;
  error: string | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface ExecutionUpdate {
  execution_id: string;
  playbook_name: string;
  status: string;
  current_step_index: number;
  total_steps: number;
  error: string | null;
  started_at: string | null;
  completed_at: string | null;
  step_results: StepResult[];
}

export interface ScreenshotFrame {
  executionId: string;
  screenshot: string; // base64 encoded JPEG
  timestamp: string;
}

export interface WebSocketMessage {
  type: 'execution_update' | 'screenshot_frame' | 'pong' | 'error';
  data?: ExecutionUpdate | ScreenshotFrame;
  error?: string;
}

// Enums
export type ExecutionStatus =
  | 'pending'
  | 'running'
  | 'paused'
  | 'completed'
  | 'failed'
  | 'cancelled';

export type StepStatus =
  | 'pending'
  | 'running'
  | 'completed'
  | 'failed'
  | 'skipped';

export type ParameterType =
  | 'string'
  | 'integer'
  | 'float'
  | 'boolean'
  | 'file'
  | 'credential'
  | 'list'
  | 'dict';
