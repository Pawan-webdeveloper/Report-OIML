// frontend/src/api/evaluations.ts — CRUD + required-tests + workflow actions
import type { Equipment, Evaluation, RequiredTestsPreview } from '../types';
import { client } from './client';

export async function listEvaluations(): Promise<Evaluation[]> {
  const { data } = await client.get('/evaluations');
  return data;
}

export async function getEvaluation(id: string): Promise<Evaluation> {
  const { data } = await client.get(`/evaluations/${id}`);
  return data;
}

export interface CreateEvaluationBody {
  instrument_id: string;
  purpose?: 'TYPE_APPROVAL' | 'VERIFICATION';
  mpe_context?: 'INITIAL' | 'IN_SERVICE';
  observer_id?: string;
}

export async function createEvaluation(body: CreateEvaluationBody): Promise<Evaluation> {
  const { data } = await client.post('/evaluations', body);
  return data;
}

export async function getRequiredTests(id: string): Promise<RequiredTestsPreview> {
  const { data } = await client.get(`/evaluations/${id}/required-tests`);
  return data;
}

export async function listEvaluationEquipment(id: string): Promise<Equipment[]> {
  const { data } = await client.get(`/evaluations/${id}/equipment`);
  return data;
}

export async function listAllEquipment(): Promise<Equipment[]> {
  const { data } = await client.get('/equipment');
  return data;
}

export async function linkEquipment(id: string, equipmentId: string): Promise<void> {
  await client.post(`/evaluations/${id}/equipment`, { equipment_id: equipmentId });
}

const post = async (id: string, path: string, body?: unknown): Promise<Evaluation> => {
  const { data } = await client.post(`/evaluations/${id}/${path}`, body ?? {});
  return data;
};

export const submitEvaluation = (id: string) => post(id, 'submit');
export const startReview = (id: string) => post(id, 'start-review');
export const returnEvaluation = (id: string, comment: string) => post(id, 'return', { comment });
export const approveEvaluation = (id: string) => post(id, 'approve');
export const reopenEvaluation = (id: string) => post(id, 'reopen');
export const archiveEvaluation = (id: string) => post(id, 'archive');