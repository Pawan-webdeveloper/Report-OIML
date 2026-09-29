// frontend/src/api/tests.ts
import type { TestRecord } from '../types';
import { client } from './client';

export interface SaveTestBody {
  kind: string;
  instance_no?: number;
  condition_label?: string | null;
  test_date?: string | null;
  observations: Record<string, unknown>;
  remarks?: string | null;
}

export async function listTestRecords(evaluationId: string): Promise<TestRecord[]> {
  const { data } = await client.get(`/evaluations/${evaluationId}/tests`);
  return data;
}

export async function saveTestRecord(
  evaluationId: string,
  body: SaveTestBody,
): Promise<TestRecord> {
  const { data } = await client.post(`/evaluations/${evaluationId}/tests`, body);
  return data;
}