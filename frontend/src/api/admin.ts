import type { Role, User } from '../types';
import { client } from './client';

// ───────────────────────────────────────────────────────────── users (ADMIN)
export async function listUsers(): Promise<User[]> {
  const { data } = await client.get('/users');
  return data;
}

export interface UserInput {
  username: string;
  full_name: string;
  email: string;
  password: string;
  role: Role;
}

export async function createUser(body: UserInput): Promise<User> {
  const { data } = await client.post('/users', body);
  return data;
}

export interface UserPatch {
  full_name?: string;
  email?: string;
  role?: Role;
  is_active?: boolean;
  new_password?: string;
}

export async function updateUser(id: string, body: UserPatch): Promise<User> {
  const { data } = await client.patch(`/users/${id}`, body);
  return data;
}

export async function unlockUser(id: string): Promise<User> {
  const { data } = await client.post(`/users/${id}/unlock`);
  return data;
}

// ───────────────────────────────────────────────────────────── audit (A/R)
export interface AuditRow {
  id: number;
  at: string;
  action: string;
  entity: string | null;
  entity_id: string | null;
  user_id: string | null;
  ip: string | null;
}

export async function listAudit(params: {
  action?: string;
  entity?: string;
  limit?: number;
  offset?: number;
}): Promise<AuditRow[]> {
  const { data } = await client.get('/audit', { params });
  return data;
}

// ─────────────────────────────────────────────────────────── rulesets (all)
export interface RulesetSummary {
  id: string;
  title: string | null;
  effective_from: string | null;
  sha256: string;
  is_active: boolean;
}

export interface RulesetDetail extends RulesetSummary {
  document: Record<string, unknown>;
}

export async function listRulesets(): Promise<RulesetSummary[]> {
  const { data } = await client.get('/rulesets');
  return data;
}

export async function getRuleset(id: string): Promise<RulesetDetail> {
  const { data } = await client.get(`/rulesets/${id}`);
  return data;
}