import axios from 'axios';
import type { User } from '../types';
import { API_BASE, client } from './client';

/** Raw instance for endpoints that must NOT trigger the refresh interceptor. */
const raw = axios.create({ baseURL: API_BASE, withCredentials: true });

export interface LoginResponse {
  access_token: string;
  token_type: string;
  must_change_password: boolean;
  user: User;
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  const { data } = await raw.post('/auth/login', { username, password });
  return data;
}

export async function refresh(): Promise<{ access_token: string }> {
  const { data } = await raw.post('/auth/refresh');
  return data;
}

export async function logout(): Promise<void> {
  await raw.post('/auth/logout');
}

export async function me(token: string): Promise<User> {
  const { data } = await raw.get('/auth/me', {
    headers: { Authorization: `Bearer ${token}` },
  });
  return data;
}

export async function changePassword(current_password: string, new_password: string) {
  const { data } = await client.post('/auth/change-password', {
    current_password,
    new_password,
  });
  return data as { message: string };
}