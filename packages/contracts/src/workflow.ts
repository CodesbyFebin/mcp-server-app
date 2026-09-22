/**
 * Workflow Contracts
 * 
 * WorkflowDefinition: Immutable specification of states and transitions
 * WorkflowInstance: Runtime execution state of a specific workflow execution
 */

export interface ExecutionFailure {
  type: string;
  message: string;
  stack?: string;
}

export interface WorkflowDefinition {
  workflowId: string;
  taskId: string;
  version: string;
  name?: string;
  description?: string;
  states: WorkflowState[];
  transitions: Transition[];
  compensation?: Compensation;
  createdAt: string;
}

export interface WorkflowState {
  name: string;
  type: 'start' | 'process' | 'approval' | 'end';
  engine?: string;
  policies?: string[];
  onEnter?: TransitionAction[];
  onExit?: TransitionAction[];
}

export interface Transition {
  from: string;
  to: string;
  engine?: string;
  policy?: string;
  timeoutMs?: number;
  onSuccess?: TransitionAction[];
  onFailure?: TransitionAction[];
}

export interface TransitionAction {
  type: 'emit-event' | 'invoke-engine' | 'notify' | 'compensate';
  target: string;
  payload?: unknown;
}

export interface Compensation {
  strategy: 'saga' | 'compensating-actions';
}

export interface WorkflowInstance {
  instanceId: string;
  definitionId: string;
  definitionVersion: string;
  status: 'created' | 'running' | 'waiting' | 'completed' | 'failed' | 'cancelled' | 'suspended';
  currentState?: string;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
  correlationId?: string;
  causationId?: string;
  assignedTask?: string;
  inputArtifactIds?: string[];
  outputArtifactIds?: string[];
  retryCount?: number;
  lastError?: ExecutionFailure;
}