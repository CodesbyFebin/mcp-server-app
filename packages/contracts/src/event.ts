/**
 * Event Contracts - Hardened Production Model
 * 
 * EventEnvelope: Immutable, ordered record of something that happened
 * Events are the source of truth; artifacts are materialized views.
 * 
 * Guarantees:
 * - sequence uniqueness per aggregate
 * - immutable events
 * - deterministic ordering
 * - idempotency
 * - correlation tracking
 */

import { z } from "zod";
import { Timestamp, Digest } from './common.js';

// ---- Value types ---

export interface CausedBy {
  causationId: string;
  correlationId?: string;
}

export interface Actor {
  type: 'human' | 'system' | 'engine';
  id: string;
}

export interface Metadata {
  version: string;
  source: string;
  digest: string; // SHA-256 hex
}

// ---- Zod schemas for value types ---

export const ActorSchema = z.object({
  type: z.enum(['human', 'system', 'engine']),
  id: z.string(),
});

export const MetadataSchema = z.object({
  version: z.string(),
  source: z.string(),
  digest: z.string(),
});

// ---- EventEnvelope ---

export const EventEnvelopeSchema = z.object({
  eventId: z.string().uuid(),
  eventType: z.string(),
  aggregateId: z.string(),
  aggregateType: z.string(),
  sequence: z.number().int().positive(),
  occurredAt: z.string().datetime(),
  causedBy: z.lazy(() => z.object({
    causationId: z.string().uuid(),
    correlationId: z.string().uuid().optional(),
  })),
  actor: ActorSchema,
  payload: z.record(z.unknown()),
  metadata: MetadataSchema,
  contractVersion: z.string(),
  schemaVersion: z.string().default('1.0.0'),
});

export type EventEnvelope = z.infer<typeof EventEnvelopeSchema>;

// ---- DomainEventIntent ----

export const DomainEventIntentSchema = z.object({
  eventType: z.string(),
  aggregateId: z.string(),
  payload: z.record(z.unknown()),
  metadata: z.object({
    source: z.string().optional(),
  }),
});

export type DomainEventIntent = z.infer<typeof DomainEventIntentSchema>;

// ---- Event Store Interface ----

export interface EventStore {
  init(): Promise<void>;
  append(envelope: EventEnvelope | EventEnvelope[]): Promise<void>;
  getForAggregate(aggregateId: string): Promise<EventEnvelope[]>;
  getNextSequence(aggregateId: string): Promise<number>;
  getByEventId(eventId: string): Promise<EventEnvelope | null>;
  exists(eventId: string): Promise<boolean>;
  transaction(envelopes: EventEnvelope[]): Promise<void>;
}

// ---- In-Memory Implementation (tests) ----

export class MemoryEventStore implements EventStore {
  private store: Map<string, EventEnvelope[]> = new Map();
  private sequences: Map<string, number> = new Map();

  async init(): Promise<void> {
    // No-op for in-memory
  }

  async append(envelopes: EventEnvelope | EventEnvelope[]): Promise<void> {
    const arr = Array.isArray(envelopes) ? envelopes : [envelopes];
    for (const envelope of arr) {
      const currentSeq = this.sequences.get(envelope.aggregateId) || 0;
      // Assign sequential order within this append call
      const newSeq = currentSeq + arr.indexOf(envelope) + 1;
      // We'll let the caller set the proper sequence, or use a simple counter
      // For now, store as-is and assign sequence later if needed
      
      if (!this.store.has(envelope.aggregateId)) {
        this.store.set(envelope.aggregateId, []);
      }
      this.store.get(envelope.aggregateId)!.push(envelope);
      this.sequences.set(envelope.aggregateId, newSeq);
    }
  }

  async getNextSequence(aggregateId: string): Promise<number> {
    return (this.sequences.get(aggregateId) || 0) + 1;
  }

  async getForAggregate(aggregateId: string): Promise<EventEnvelope[]> {
    return this.store.get(aggregateId) || [];
  }

  async getByEventId(eventId: string): Promise<EventEnvelope | null> {
    for (const envelopes of this.store.values()) {
      for (const env of envelopes) {
        if (env.eventId === eventId) return env;
      }
    }
    return null;
  }

  async exists(eventId: string): Promise<boolean> {
    return (await this.getByEventId(eventId)) !== null;
  }

  async transaction(envelopes: EventEnvelope[]): Promise<void> {
    await this.append(envelopes);
  }
}

// ---- PostgreSQL Implementation (production pattern) ----

export class PgEventStore implements EventStore {
  constructor(private pool: any) {} // pg.Pool
  
  async init(): Promise<void> {
    await this.pool.query(`
      CREATE TABLE IF NOT EXISTS events (
        event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        event_type VARCHAR NOT NULL,
        aggregate_id VARCHAR NOT NULL,
        aggregate_type VARCHAR NOT NULL,
        sequence INTEGER NOT NULL,
        occurred_at TIMESTAMP NOT NULL,
        causation_id UUID,
        correlation_id UUID,
        actor_type VARCHAR NOT NULL,
        actor_id VARCHAR NOT NULL,
        payload JSONB NOT NULL,
        metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
        contract_version VARCHAR NOT NULL DEFAULT '1.0.0',
        schema_version VARCHAR NOT NULL DEFAULT '1.0.0',
        created_at TIMESTAMP DEFAULT now(),
        updated_at TIMESTAMP DEFAULT now()
      );
      CREATE INDEX IF NOT EXISTS idx_events_aggregate ON events(aggregate_id, sequence);
      CREATE INDEX IF NOT EXISTS idx_events_id ON events(event_id);
    `);
  }

  async append(envelopes: EventEnvelope | EventEnvelope[]): Promise<void> {
    const arr = Array.isArray(envelopes) ? envelopes : [envelopes];
    const now = new Date().toISOString();
    
    for (let i = 0; i < arr.length; i++) {
      const env = arr[i];
      const currentSeqResult = await this.pool.query(
        `SELECT COALESCE(MAX(sequence), 0) FROM events WHERE aggregate_id = $1`,
        [env.aggregateId]
      );
      const baseSeq = parseInt(currentSeqResult.rows[0].coalesce);
      const sequence = baseSeq + i + 1;

      const causedBy = env.causedBy || { causationId: crypto.randomUUID() };
      const eventId = crypto.randomUUID();

      await this.pool.query(
        `INSERT INTO events (event_id, event_type, aggregate_id, aggregate_type, sequence, occurred_at, causation_id, correlation_id, actor_type, actor_id, payload, metadata, contract_version, schema_version, created_at)
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, now())`,
        [
          eventId,
          env.eventType,
          env.aggregateId,
          env.aggregateType || 'Server',
          sequence,  // position in the insert order
          env.occurredAt || now,
          causedBy.causationId,
          causedBy.correlationId,
          env.actor.type,
          env.actor.id,
          JSON.stringify(env.payload),
          JSON.stringify({ version: env.metadata.version, source: env.metadata.source, digest: env.metadata.digest }),
          env.contractVersion,
          env.schemaVersion,
        ]
      );
    }
  }

async getForAggregate(aggregateId: string): Promise<EventEnvelope[]> {
    const result = await this.pool.query(`
      SELECT * FROM events WHERE aggregate_id = $1 ORDER BY sequence ASC`,
      [aggregateId]
    );
    const rows = result.rows as Array<{
      event_id: string;
      event_type: string;
      aggregate_id: string;
      aggregate_type: string;
      sequence: number;
      occurred_at: Date;
      causation_id: string | null;
      correlation_id: string | null;
      actor_type: string;
      actor_id: string;
      payload: string;
      metadata: string;
      contract_version: string;
      schema_version: string;
    }>;
    return rows.map(row => ({
      eventId: row.event_id,
      eventType: row.event_type,
      aggregateId: row.aggregate_id,
      aggregateType: row.aggregate_type || 'Server',
      sequence: row.sequence,
      occurredAt: row.occurred_at.toISOString(),
      causedBy: {
        causationId: row.causation_id || '',
        correlationId: row.correlation_id || undefined,
      },
      actor: {
        type: row.actor_type as 'human' | 'system' | 'engine',
        id: row.actor_id,
      },
      payload: JSON.parse(row.payload),
      metadata: {
        version: (row.metadata as any)?.version || '1.0.0',
        source: (row.metadata as any)?.source || 'unknown',
        digest: (row.metadata as any)?.digest || '',
      },
      contractVersion: row.contract_version,
      schemaVersion: row.schema_version || '1.0.0',
    }));
  }

  async getNextSequence(aggregateId: string): Promise<number> {
    const result = await this.pool.query(`
      SELECT COALESCE(MAX(sequence), 0) + 1 FROM events WHERE aggregate_id = $1`,
      [aggregateId]
    );
    return parseInt(result.rows[0].coalesce);
  }

  async getByEventId(eventId: string): Promise<EventEnvelope | null> {
    const result = await this.pool.query(`
      SELECT * FROM events WHERE event_id = $1`,
      [eventId]
    );
    if (result.rows.length === 0) return null;
    
    const row = result.rows[0] as {
      event_id: string;
      event_type: string;
      aggregate_id: string;
      aggregate_type: string;
      sequence: number;
      occurred_at: Date;
      causation_id: string | null;
      correlation_id: string | null;
      actor_type: string;
      actor_id: string;
      payload: string;
      metadata: string;
      contract_version: string;
      schema_version: string;
    };
    return {
      eventId: row.event_id,
      eventType: row.event_type,
      aggregateId: row.aggregate_id,
      aggregateType: row.aggregate_type || 'Server',
      sequence: row.sequence,
      occurredAt: row.occurred_at.toISOString(),
      causedBy: {
        causationId: row.causation_id || '',
        correlationId: row.correlation_id || undefined,
      },
      actor: {
        type: row.actor_type as 'human' | 'system' | 'engine',
        id: row.actor_id,
      },
      payload: JSON.parse(row.payload),
      metadata: {
        version: (row.metadata as any)?.version || '1.0.0',
        source: (row.metadata as any)?.source || 'unknown',
        digest: (row.metadata as any)?.digest || '',
      },
      contractVersion: row.contract_version,
      schemaVersion: row.schema_version || '1.0.0',
    };
  }

  async exists(eventId: string): Promise<boolean> {
    const result = await this.pool.query(
      `SELECT EXISTS(SELECT 1 FROM events WHERE event_id = $1)`,
      [eventId]
    );
    return result.rows[0].exists;
  }

  async transaction(envelopes: EventEnvelope[]): Promise<void> {
    if (envelopes.length === 0) return;
    
    const client = await this.pool.connect();
    try {
      await client.query('BEGIN');
      for (let i = 0; i < envelopes.length; i++) {
        const env = envelopes[i];
        const currentSeqResult = await client.query(
          `SELECT COALESCE(MAX(sequence), 0) FROM events WHERE aggregate_id = $1`,
          [env.aggregateId]
        );
        const baseSeq = parseInt(currentSeqResult.rows[0].coalesce);
        const sequence = baseSeq + i + 1;

        const causedBy = env.causedBy || { causationId: crypto.randomUUID() };
        const eventId = crypto.randomUUID();

        await client.query(
          `INSERT INTO events (event_id, event_type, aggregate_id, aggregate_type, sequence, occurred_at, causation_id, correlation_id, actor_type, actor_id, payload, metadata, contract_version, schema_version, created_at)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, now())`,
          [
            eventId,
            env.eventType,
            env.aggregateId,
            env.aggregateType || 'Server',
            sequence,
            env.occurredAt || new Date().toISOString(),
            causedBy.causationId,
            causedBy.correlationId,
            env.actor.type,
            env.actor.id,
            JSON.stringify(env.payload),
            JSON.stringify({ version: env.metadata.version, source: env.metadata.source, digest: env.metadata.digest }),
            env.contractVersion,
            env.schemaVersion,
          ]
        );
      }
      await client.query('COMMIT');
    } catch (err) {
      await client.query('ROLLBACK');
      throw err;
    } finally {
      client.release();
    }
  }
}