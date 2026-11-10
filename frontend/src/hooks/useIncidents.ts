import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import incidentsService from '../services/incidents.service';
import type { IncidentCreate, IncidentUpdateSchema, IncidentQueryParams, UpdateType } from '../types';

export function useIncidents(params: IncidentQueryParams = {}) {
  return useQuery({
    queryKey: ['incidents', params],
    queryFn: () => incidentsService.listIncidents(params),
  });
}

export function useIncident(id: number) {
  return useQuery({
    queryKey: ['incident', id],
    queryFn: () => incidentsService.getIncident(id),
    enabled: !!id,
  });
}

export function useCreateIncident() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: IncidentCreate) => incidentsService.createIncident(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['incidents'] }),
  });
}

export function useUpdateIncident(id: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: IncidentUpdateSchema) => incidentsService.updateIncident(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['incidents'] });
      qc.invalidateQueries({ queryKey: ['incident', id] });
    },
  });
}

export function useAssignIncident(id: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (userId: number) => incidentsService.assignIncident(id, userId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['incident', id] }),
  });
}

export function useAddIncidentUpdate(id: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ message, updateType }: { message: string; updateType?: UpdateType }) =>
      incidentsService.addIncidentUpdate(id, message, updateType),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['incident', id] }),
  });
}

export function useResolveIncident(id: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (notes?: string) => incidentsService.resolveIncident(id, notes),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['incidents'] });
      qc.invalidateQueries({ queryKey: ['incident', id] });
    },
  });
}

export function useCloseIncident(id: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => incidentsService.closeIncident(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['incidents'] });
      qc.invalidateQueries({ queryKey: ['incident', id] });
    },
  });
}
