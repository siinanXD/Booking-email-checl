import { apiClient } from "@/lib/api/client";
import type {
  TenantWorkflowCreateRequest,
  TenantWorkflowListResponse,
  TenantWorkflowPreviewRequest,
  TenantWorkflowPreviewResponse,
  TenantWorkflowResponse,
  TenantWorkflowRunTestsResponse,
  TenantWorkflowSuggestRequest,
  TenantWorkflowSuggestResponse,
  TenantWorkflowUpdateRequest,
} from "@/lib/types/api";

export interface WorkflowApiClient {
  fetchWorkflows: () => Promise<TenantWorkflowListResponse>;
  fetchWorkflow: (id: string) => Promise<TenantWorkflowResponse>;
  createWorkflow: (payload: TenantWorkflowCreateRequest) => Promise<TenantWorkflowResponse>;
  updateWorkflow: (
    id: string,
    payload: TenantWorkflowUpdateRequest
  ) => Promise<TenantWorkflowResponse>;
  deleteWorkflow: (id: string) => Promise<void>;
  suggestWorkflow: (
    payload: TenantWorkflowSuggestRequest
  ) => Promise<TenantWorkflowSuggestResponse>;
  previewWorkflow: (
    id: string,
    payload: TenantWorkflowPreviewRequest
  ) => Promise<TenantWorkflowPreviewResponse>;
  runWorkflowTests: (id: string) => Promise<TenantWorkflowRunTestsResponse>;
}

function basePath(adminAccountId?: string): string {
  if (adminAccountId) {
    return `/api/admin/accounts/${adminAccountId}/workflows`;
  }
  return "/api/workflows";
}

export function createWorkflowApi(adminAccountId?: string): WorkflowApiClient {
  const base = basePath(adminAccountId);
  return {
    fetchWorkflows: async () => {
      const { data } = await apiClient.get<TenantWorkflowListResponse>(base);
      return data;
    },
    fetchWorkflow: async (id) => {
      const { data } = await apiClient.get<TenantWorkflowResponse>(`${base}/${id}`);
      return data;
    },
    createWorkflow: async (payload) => {
      const { data } = await apiClient.post<TenantWorkflowResponse>(base, payload);
      return data;
    },
    updateWorkflow: async (id, payload) => {
      const { data } = await apiClient.put<TenantWorkflowResponse>(
        `${base}/${id}`,
        payload
      );
      return data;
    },
    deleteWorkflow: async (id) => {
      await apiClient.delete(`${base}/${id}`);
    },
    suggestWorkflow: async (payload) => {
      const { data } = await apiClient.post<TenantWorkflowSuggestResponse>(
        `${base}/suggest`,
        payload
      );
      return data;
    },
    previewWorkflow: async (id, payload) => {
      const { data } = await apiClient.post<TenantWorkflowPreviewResponse>(
        `${base}/${id}/preview`,
        payload
      );
      return data;
    },
    runWorkflowTests: async (id) => {
      const { data } = await apiClient.post<TenantWorkflowRunTestsResponse>(
        `${base}/${id}/run-tests`
      );
      return data;
    },
  };
}

const tenantApi = createWorkflowApi();

export const fetchWorkflows = tenantApi.fetchWorkflows;
export const fetchWorkflow = tenantApi.fetchWorkflow;
export const createWorkflow = tenantApi.createWorkflow;
export const updateWorkflow = tenantApi.updateWorkflow;
export const deleteWorkflow = tenantApi.deleteWorkflow;
export const suggestWorkflow = tenantApi.suggestWorkflow;
export const previewWorkflow = tenantApi.previewWorkflow;
export const runWorkflowTests = tenantApi.runWorkflowTests;
