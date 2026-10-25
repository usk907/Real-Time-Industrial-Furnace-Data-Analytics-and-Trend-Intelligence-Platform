import { api } from './client';

export interface ChatMessage {
  role: 'user' | 'model';
  content: string;
}

export interface ChatResponse {
  response: string;
  offline: boolean;
}

export interface AiQueryResponse {
  question: string;
  sql: string | null;
  error: string | null;
  rows: any[];
  answer: string | null;
}

export function postChat(message: string, history: ChatMessage[] = []) {
  return api.post<ChatResponse>('/api/chat', { message, history });
}

export function postAiQuery(question: string) {
  return api.post<AiQueryResponse>('/api/ai/query', { question });
}
