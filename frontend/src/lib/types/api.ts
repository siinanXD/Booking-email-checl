export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserResponse {
  id: string;
  email: string;
  role: string;
  account_id?: string | null;
  first_name?: string | null;
  last_name?: string | null;
  account_status?: string | null;
  account_display_name?: string | null;
  mail_connection_status?: string | null;
  mail_onboarding_completed?: boolean | null;
}

export interface ImapPresetItem {
  id: string;
  label: string;
  host: string;
  port: number;
  use_ssl: boolean;
}

export interface MailConnectionResponse {
  provider: "outlook" | "imap" | string;
  status: string;
  email_address: string;
  preset?: string | null;
  imap_host: string;
  imap_port: number;
  imap_username: string;
  imap_password_set: boolean;
  imap_use_ssl: boolean;
  outlook_auth_mode: string;
  outlook_mailbox: string;
  outlook_oauth_connected?: boolean;
  last_error?: string | null;
  last_sync_at?: string | null;
  onboarding_completed: boolean;
  imap_presets: ImapPresetItem[];
}

export interface MailTestResponse {
  success: boolean;
  message: string;
  mailbox_count?: number | null;
}

export interface MailSyncResponse {
  success: boolean;
  processed: number;
  duplicates: number;
  error_count: number;
  reprocessed?: number;
  message: string;
  last_sync_at?: string | null;
  item_errors?: string[];
  reprocess_errors?: string[];
}

export interface RegisterRequest {
  email: string;
  password: string;
  password_confirm: string;
  first_name: string;
  last_name: string;
  phone: string;
  account_type: "private" | "business";
  company_name?: string;
}

export interface RegisterResponse {
  message: string;
  account_id: string;
  status: string;
}

export interface AccountListItem {
  id: string;
  display_name: string;
  contact_email: string;
  account_type: string;
  company_name?: string | null;
  phone?: string | null;
  status: string;
  rejection_reason?: string | null;
  created_at: string;
}

export interface AccountListResponse {
  items: AccountListItem[];
  total: number;
}

export interface AdminMeResponse {
  id: string;
  email: string;
  role: string;
  account_id?: string | null;
  mail_onboarding_required: boolean;
}

export type AdminWhatsAppTestTemplate =
  | "hello_world"
  | "cleaning_task"
  | "status_notice"
  | "guest_inquiry";

export interface AdminWhatsAppInfoResponse {
  whatsapp_enabled: boolean;
  access_token_configured: boolean;
  phone_number_id: string;
  test_recipient: string;
  template_language: string;
  templates: Record<string, string>;
}

export interface AdminWhatsAppTestResponse {
  success: boolean;
  template: AdminWhatsAppTestTemplate;
  template_name?: string | null;
  provider_message_id?: string | null;
  error?: string | null;
}

export type ActivityStatus = "active" | "idle" | "never";

export interface AdminTenantRow {
  account: AccountListItem;
  activity_status: ActivityStatus;
  costs_30d_usd: number;
  tokens_30d: number;
  mails_processed_30d: number;
  last_sync_at: string | null;
  last_mail_received_at: string | null;
}

export interface AdminOverviewResponse {
  total_accounts: number;
  pending_accounts: number;
  active_accounts: number;
  active_users_7d: number;
  total_cost_usd_30d: number;
  total_tokens_30d: number;
  mails_processed_30d: number;
  tenants: AdminTenantRow[];
}

export interface AdminUserSummary {
  id: string;
  email: string;
  role: string;
  created_at: string;
}

export interface MailConnectionSummary {
  provider: string;
  status: string;
  email_address: string;
  connected: boolean;
  last_sync_at: string | null;
  last_error: string | null;
  onboarding_completed: boolean;
}

export interface AdminAccountDetailResponse {
  account: AccountListItem;
  users: AdminUserSummary[];
  mail_connection: MailConnectionSummary | null;
  activity_status: ActivityStatus;
  db_counts: Record<string, number>;
  costs_30d_usd: number;
  tokens_30d: number;
  mails_processed_30d: number;
  last_mail_received_at: string | null;
  latest_correlation_id: string | null;
  langfuse_session_url: string | null;
}

export interface AdminAccountCostRow {
  account_id: string;
  display_name: string;
  cost_usd: number;
  total_tokens: number;
  mail_count: number;
}

export interface AdminExpensiveMailRow {
  correlation_id: string;
  account_id: string | null;
  cost_usd: number;
  total_tokens: number;
  processed_at: string;
  langfuse_session_url: string | null;
}

export interface AdminCostsMetricsResponse {
  days: number;
  series: CostSeriesPoint[];
  total_usd: number;
  by_account: AdminAccountCostRow[];
  top_mails: AdminExpensiveMailRow[];
}

export interface AdminTokensMetricsResponse {
  days: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  by_account: AdminAccountCostRow[];
}

export interface AdminPublicConfigResponse {
  langfuse_host: string;
  langfuse_project_id: string | null;
  langfuse_tracing_enabled: boolean;
}

export type AdminLlmPreviewStep = "classify" | "extract";

export interface AdminLlmConfigResponse {
  classify_temperature: number;
  extract_temperature: number;
  draft_temperature: number;
  similarity_top_k: number;
  classify_prompt_override: string | null;
  extract_prompt_override: string | null;
  draft_prompt_override: string | null;
  default_classify_prompt: string;
  default_extract_prompt: string;
  default_draft_prompt: string;
  updated_at: string | null;
  updated_by_user_id: string | null;
}

export interface AdminLlmConfigUpdateRequest {
  classify_temperature: number;
  extract_temperature: number;
  draft_temperature: number;
  similarity_top_k: number;
  classify_prompt_override?: string | null;
  extract_prompt_override?: string | null;
  draft_prompt_override?: string | null;
}

export interface AdminLlmPreviewRequest {
  step?: AdminLlmPreviewStep;
  subject?: string;
  body?: string;
}

export interface AdminLlmPreviewResponse {
  step: AdminLlmPreviewStep;
  success: boolean;
  result: string | null;
  error: string | null;
  model: string;
}

export type AdminLlmPromptType = "classify" | "extract" | "draft";

export interface AdminLlmPromptHistoryEntry {
  id: string;
  prompt_type: AdminLlmPromptType;
  prompt_text: string | null;
  user_id: string | null;
  created_at: string;
}

export interface AdminLlmPromptHistoryResponse {
  prompt_type: AdminLlmPromptType;
  entries: AdminLlmPromptHistoryEntry[];
}

export interface DashboardStats {
  total_emails_today: number;
  total_emails_week: number;
  pending_review: number;
  processed_today: number;
  spam_discarded_today: number;
  new_bookings_today: number;
  cancellations_today: number;
  changes_today: number;
  booking_emails_total: number;
  booking_emails_week: number;
  cost_today_usd: number;
  cost_week_usd: number;
  avg_cost_per_mail_usd: number;
  grounding_failures_today: number;
  reviewed_today: number;
  last_sync_at?: string | null;
  last_email_received_at?: string | null;
  last_booking_detected_at?: string | null;
  mail_fetch_unread_only?: boolean;
}

export interface EmailListItem {
  correlation_id: string;
  message_id: string;
  subject: string;
  from_address: string;
  received_at: string | null;
  platform: string | null;
  intent: string | null;
  booking_number: string | null;
  processing_state: string;
  review_status: string | null;
  grounding_flag: boolean;
}

export interface EmailListResponse {
  items: EmailListItem[];
  total: number;
  page: number;
  pages: number;
}

export interface EmailDetail extends EmailListItem {
  to_addresses: string[];
  body_text: string;
  draft_body: string;
  extraction: Record<string, unknown> | null;
  approved_body: string | null;
}

export interface CostSeriesPoint {
  date: string;
  cost_usd: number;
  total_tokens: number;
  mail_count: number;
}

export interface CostsResponse {
  series: CostSeriesPoint[];
  total_usd: number;
}

export interface ReviewQueueItem {
  correlation_id: string;
  message_id: string;
  subject: string;
  from_address: string;
  intent: string | null;
  draft_body: string;
  grounding_flag: boolean;
  review_status: string;
  received_at: string | null;
}

export interface ReviewQueueResponse {
  items: ReviewQueueItem[];
  total: number;
}

export interface PropertyRecipientItem {
  property_name: string;
  phones: string[];
}

export interface UserProfileSettings {
  whatsapp_phone_e164: string | null;
  whatsapp_enabled: boolean;
}

export interface PlatformSettingsResponse {
  whatsapp_enabled: boolean;
  whatsapp_access_token_set: boolean;
  whatsapp_phone_number_id: string;
  whatsapp_api_version: string;
  whatsapp_template_language: string;
  whatsapp_template_cleaning_task: string;
  whatsapp_template_status_notice: string;
  whatsapp_template_guest_inquiry: string;
  whatsapp_default_recipients: string;
  whatsapp_test_recipient: string;
  outlook_mailbox: string;
  property_recipients: PropertyRecipientItem[];
  user_profile: UserProfileSettings;
}

export interface PlatformSettingsUpdate {
  whatsapp_enabled?: boolean;
  whatsapp_access_token?: string;
  whatsapp_phone_number_id?: string;
  whatsapp_api_version?: string;
  whatsapp_template_language?: string;
  whatsapp_template_cleaning_task?: string;
  whatsapp_template_status_notice?: string;
  whatsapp_template_guest_inquiry?: string;
  whatsapp_default_recipients?: string;
  whatsapp_test_recipient?: string;
  outlook_mailbox?: string;
  property_recipients?: PropertyRecipientItem[];
  user_profile?: UserProfileSettings;
}

export interface WhatsAppTestResponse {
  success: boolean;
  provider_message_id?: string | null;
  error?: string | null;
}

export interface WipeDataResponse {
  deleted: Record<string, number>;
}

export type WorkflowImportance = "high" | "medium" | "low";
export type WorkflowLlmProvider = "openai" | "gemini";

export interface WorkflowMatchRules {
  subject_keywords: string[];
  from_domains: string[];
  body_keywords: string[];
}

export interface WorkflowTestEmail {
  subject: string;
  body: string;
  expected_fields?: Record<string, unknown> | null;
}

export interface WorkflowFewShotExample {
  subject: string;
  body: string;
  expected_json: Record<string, unknown>;
}

export interface TenantWorkflowSummary {
  id: string;
  slug: string;
  label: string;
  description: string;
  enabled: boolean;
  sandbox_only: boolean;
  importance: WorkflowImportance;
  supports_multimodal: boolean;
  test_email_count: number;
  tests_passed: boolean;
  updated_at: string;
}

export interface TenantWorkflowListResponse {
  items: TenantWorkflowSummary[];
}

export interface TenantWorkflowResponse {
  id: string;
  account_id: string;
  slug: string;
  label: string;
  description: string;
  enabled: boolean;
  sandbox_only: boolean;
  priority: number;
  search_hints: string;
  importance: WorkflowImportance;
  required_fields: string[];
  optional_fields: string[];
  extraction_schema: Record<string, unknown>;
  classify_prompt: string;
  extract_prompt: string;
  draft_prompt: string;
  few_shot_examples: WorkflowFewShotExample[];
  test_emails: WorkflowTestEmail[];
  match_rules: WorkflowMatchRules;
  llm_provider: WorkflowLlmProvider;
  supports_multimodal: boolean;
  multimodal_prompt: string;
  last_test_passed_at: string | null;
  last_test_passed_count: number;
  last_test_passed_total: number;
  created_by_user_id: string | null;
  updated_by_user_id: string | null;
  created_at: string;
  updated_at: string;
  version: number;
}

export interface TenantWorkflowCreateRequest {
  label: string;
  slug?: string | null;
  description?: string;
  search_hints?: string;
  importance?: WorkflowImportance;
  required_fields?: string[];
  optional_fields?: string[];
  extraction_schema?: Record<string, unknown>;
  classify_prompt?: string;
  extract_prompt?: string;
  draft_prompt?: string;
  few_shot_examples?: WorkflowFewShotExample[];
  test_emails?: WorkflowTestEmail[];
  match_rules?: WorkflowMatchRules;
  llm_provider?: WorkflowLlmProvider;
  supports_multimodal?: boolean;
  multimodal_prompt?: string;
  enabled?: boolean;
  sandbox_only?: boolean;
  priority?: number;
}

export type TenantWorkflowUpdateRequest = TenantWorkflowCreateRequest;

export interface TenantWorkflowSuggestRequest {
  description: string;
  label_hint?: string | null;
}

export interface TenantWorkflowSuggestResponse {
  label: string;
  slug: string;
  description: string;
  search_hints: string;
  importance: WorkflowImportance;
  required_fields: string[];
  optional_fields: string[];
  extraction_schema: Record<string, unknown>;
  classify_prompt: string;
  extract_prompt: string;
  match_rules: WorkflowMatchRules;
  test_emails: WorkflowTestEmail[];
  llm_provider: WorkflowLlmProvider;
  supports_multimodal: boolean;
}

export interface TenantWorkflowPreviewRequest {
  subject?: string;
  body?: string;
}

export interface TenantWorkflowPreviewResponse {
  success: boolean;
  result: string | null;
  error: string | null;
  model: string;
}

export interface TenantWorkflowTestCaseResult {
  subject: string;
  success: boolean;
  result: string | null;
  error: string | null;
}

export interface TenantWorkflowRunTestsResponse {
  workflow_id: string;
  total: number;
  passed: number;
  results: TenantWorkflowTestCaseResult[];
}

export interface ApiError {
  error: string;
  code: number;
}
