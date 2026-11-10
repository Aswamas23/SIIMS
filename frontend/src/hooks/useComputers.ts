import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import computersService from '../services/computers.service';
import type { ComputerCreate, ComputerUpdate, ComputerQueryParams } from '../types';

export function useComputers(params: ComputerQueryParams = {}) {
  return useQuery({
    queryKey: ['computers', params],
    queryFn: () => computersService.listComputers(params),
  });
}

export function useComputer(id: number) {
  return useQuery({
    queryKey: ['computer', id],
    queryFn: () => computersService.getComputer(id),
    enabled: !!id,
  });
}

export function useCreateComputer() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ComputerCreate) => computersService.createComputer(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['computers'] }),
  });
}

export function useUpdateComputer(id: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ComputerUpdate) => computersService.updateComputer(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['computers'] });
      qc.invalidateQueries({ queryKey: ['computer', id] });
    },
  });
}

export function useDeactivateComputer() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => computersService.deactivateComputer(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['computers'] }),
  });
}
