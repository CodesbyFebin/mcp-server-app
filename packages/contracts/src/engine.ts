/**
 * Engine Contracts
 * 
 * EventStore: Interface for event storage implementations
 * Provides methods for appending, retrieving, and tracking events
 */

export interface EventStore {
  init(): Promise<void>;
  append(envelope: import('./event.ts').EventEnvelope | import('./event.ts').EventEnvelope[]): Promise<void>;
  getForAggregate(aggregateId: string): Promise<import('./event.ts').EventEnvelope[]>;
  getNextSequence(): Promise<number>;
}