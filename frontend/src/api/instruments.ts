// frontend/src/api/instruments.ts
import type { Instrument } from '../types';
import { client } from './client';

export interface RangePayload {
  e: string;
  d: string;
  max: string;
}

export interface InstrumentPayload {
  type_designation: string;
  application_no?: string | null;
  category?: string | null;
  manufacturer_id?: string | null;
  accuracy_class: string;
  unit: string;
  min_capacity: string;
  power_supply_category?: string[];
  printer?: string | null;
  direct_sales_to_public?: boolean;
  level_indicator?: boolean | null;
  zero_devices?: Record<string, boolean>;
  tare_devices?: Record<string, boolean>;
  remarks?: string | null;
  ranges: RangePayload[];
}

export async function listInstruments(q?: string): Promise<Instrument[]> {
  const { data } = await client.get('/instruments', { params: q ? { q } : {} });
  return data;
}

export async function getInstrument(id: string): Promise<Instrument> {
  const { data } = await client.get(`/instruments/${id}`);
  return data;
}

export async function createInstrument(body: InstrumentPayload): Promise<Instrument> {
  const { data } = await client.post('/instruments', body);
  return data;
}

export async function updateInstrument(
  id: string,
  body: Partial<InstrumentPayload>,
): Promise<Instrument> {
  const { data } = await client.patch(`/instruments/${id}`, body);
  return data;
}