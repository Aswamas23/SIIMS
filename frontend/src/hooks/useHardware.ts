import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import hardwareService from '../services/hardware.service';
import type { ThresholdUpdate } from '../types';

export function useHardwareMetrics(params: { skip?: number; limit?: number } = {}) {
  return useQuery({
    queryKey: ['hardware-metrics', params],
    queryFn: () => hardwareService.getHardwareMetrics(params),
    refetchInterval: 30_000,
  });
}

export function useHardwareAlerts() {
  return useQuery({
    queryKey: ['hardware-alerts'],
    queryFn: () => hardwareService.getHardwareAlerts(),
    refetchInterval: 30_000,
  });
}

export function useThresholds() {
  return useQuery({
    queryKey: ['thresholds'],
    queryFn: () => hardwareService.getThresholds(),
  });
}

export function useUpdateThresholds() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ThresholdUpdate) => hardwareService.updateThresholds(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['thresholds'] }),
  });
}
