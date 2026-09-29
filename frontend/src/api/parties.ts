// frontend/src/api/parties.ts
import type { Party } from '../types';
import { client } from './client';

export async function listParties(): Promise<Party[]> {
  const { data } = await client.get('/parties');
  return data;
}

export async function createParty(body: Partial<Party>): Promise<Party> {
  const { data } = await client.post('/parties', body);
  return data;
}