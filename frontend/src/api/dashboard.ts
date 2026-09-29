import { client } from './client';

export interface DashboardKpis {
  totals: {
    evaluations: number;
    instruments: number;
    users: number;
    test_records: number;
  };
  status_counts: Record<string, number>;
  outcome_counts: Record<string, number>;
  trend: { month: string; count: number }[];
  failures: { kind: string; count: number }[];
}

export async function getKpis(): Promise<DashboardKpis> {
  const { data } = await client.get('/dashboard/kpis');
  return data;
}