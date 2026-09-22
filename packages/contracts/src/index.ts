/**
 * MCP Servers Contracts - Public API
 * 
 * Exports all shared TypeScript schemas and interfaces for the MCP ecosystem.
 * This package serves as the foundation for content contracts (Phase A) and
 * registry contracts (Phase B) per SAFE-DEEP OS v5 architecture.
 */

export { EventStore } from './engine.js';
export { EventEnvelope } from './event.js';
export { DomainEventIntent } from './event.js';
export { WorkflowDefinition, WorkflowInstance, WorkflowState, Transition, TransitionAction, Compensation } from './workflow.js';
export type { Timestamp, Digest } from './common.js';