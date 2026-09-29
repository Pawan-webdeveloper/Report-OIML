import { client } from './client';

export interface ExportInfo {
  id: string;
  format: 'PDF' | 'DOCX';
  version: number;
  sha256: string;
  signed: boolean;
  created_at: string;
}

export interface ExportResult {
  id: string;
  format: string;
  version: number;
  sha256: string;
  size_bytes: number;
  download_url: string;
}

export const printPath = (evaluationId: string) =>
  `/evaluations/${evaluationId}/report/print`;

export const exportDownloadPath = (evaluationId: string, exportId: string) =>
  `/evaluations/${evaluationId}/report/exports/${exportId}/download`;

export async function exportReport(
  evaluationId: string,
  format: 'PDF' | 'DOCX',
): Promise<ExportResult> {
  const { data } = await client.post(`/evaluations/${evaluationId}/report/export`, {
    format,
  });
  return data;
}

export async function listExports(evaluationId: string): Promise<ExportInfo[]> {
  const { data } = await client.get(`/evaluations/${evaluationId}/report/exports`);
  return data;
}