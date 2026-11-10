import api from './api';
import type { SystemSetting, SettingUpdate, EmailTestResponse } from '../types';

export async function getSettings(): Promise<SystemSetting[]> {
  const res = await api.get<SystemSetting[]>('/api/v1/settings/');
  return res.data;
}

export async function updateSettings(settings: SettingUpdate[]): Promise<SystemSetting[]> {
  const res = await api.put<SystemSetting[]>('/api/v1/settings/', { settings });
  return res.data;
}

export async function testEmail(): Promise<EmailTestResponse> {
  const res = await api.get<EmailTestResponse>('/api/v1/settings/email-test');
  return res.data;
}

export default { getSettings, updateSettings, testEmail };
