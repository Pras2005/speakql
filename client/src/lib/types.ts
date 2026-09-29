export type WorkspaceRole = 'admin' | 'compliance_admin' | 'analyst' | 'viewer';
export type AccessLevel = 'discover' | 'query' | 'export' | 'manage';

export interface AuthTokenResponse {
  access_token: string;
}

export interface LoginPayload {
  username: string;
  password: string;
}

export interface SignupPayload {
  username: string;
  password: string;
}

export interface CurrentUser {
  username: string;
  user_id: number;
  org_id?: number | null;
  org_name?: string | null;
  workspace_id?: number | null;
  workspace_name?: string | null;
  role?: WorkspaceRole | null;
}

export interface Membership {
  id: number;
  org_id: number;
  workspace_id: number;
  role: WorkspaceRole;
}

export interface Database {
  id: number;
  user_id: number;
  host: string | null;
  port: number | null;
  db_user: string | null;
  db_name: string;
  name?: string | null;
  access_level?: AccessLevel | null;
  connection_status?: string | null;
  workspace_id?: number | null;
  created_at: string;
}

export interface DatabaseCreatePayload {
  host?: string;
  port?: number | null;
  db_user?: string;
  db_password: string;
  db_name: string;
}

export interface DatabaseUpdatePayload {
  host?: string;
  port?: number | null;
  db_user?: string;
  db_password?: string;
  db_name?: string;
}

export interface DatabaseGrant {
  id: number;
  workspace_id: number;
  database_id: number;
  user_id: number;
  access_level: AccessLevel;
  granted_by: number;
  created_at: string;
  updated_at: string;
}

export interface CreateGrantPayload {
  user_id: number;
  access_level: AccessLevel;
}

export interface UpdateGrantPayload {
  access_level: AccessLevel;
}

export interface QueryHistoryItem {
  id: number;
  db_id: number;
  prompt: string | null;
  raw_sql: string | null;
  status: string;
  error: string | null;
  timestamp: string;
}

export interface GenerateSqlPayload {
  prompt: string;
  db_id: number;
  provider_type?: 'gemini' | 'local' | 'openai';
  model_name?: string;
}

export interface GenerateSqlResponse {
  raw_sql: string;
  confirmation_required: boolean;
  message?: string | null;
}

export interface ExecuteSqlPayload {
  raw_sql: string;
  db_id: number;
  original_prompt?: string;
  generated_sql?: string;
  sql_rationale?: string;
}

export interface PolicyOutcome {
  allowed: boolean;
  reason: string;
  policy_id?: number | null;
}

export interface RiskMetadata {
  score: number;
  flags: string[];
}

export interface ExplainabilityPayload {
  sql_rationale?: string | null;
  tables_referenced: string[];
  policy_outcome: PolicyOutcome;
  risk_metadata: RiskMetadata;
  confidence_score: number;
  needs_review: boolean;
}

export interface GovernedQueryResponse {
  status: string;
  result?: Record<string, unknown>[] | null;
  explainability: ExplainabilityPayload;
  error?: string | null;
  approval_id?: number;
}

export interface SchemaVisualization {
  schemas: string[];
  tables: Record<
    string,
    {
      structure?: {
        schema: string;
        table_name: string;
        columns: Array<{
          name: string;
          type: string;
          nullable: boolean;
          primary_key: boolean;
          comment?: string | null;
        }>;
      };
      sample_data?: Record<string, unknown>[];
      error?: string;
    }
  >;
}

export interface CatalogEntry {
  id: number;
  workspace_id: number;
  db_id: number;
  table_name: string;
  description?: string | null;
  owner?: string | null;
  freshness?: string | null;
  status: 'draft' | 'published';
}

export interface BusinessTerm {
  id: number;
  term: string;
  definition: string;
  maps_to_table?: string | null;
  maps_to_column?: string | null;
}

export interface MetricDefinition {
  id: number;
  name: string;
  sql_expression: string;
  description?: string | null;
  status: 'draft' | 'certified';
}

export interface PublishTablePayload {
  db_id: number;
  table_name: string;
  description: string;
}

export interface BusinessTermPayload {
  term: string;
  definition: string;
  maps_to_table?: string;
  maps_to_column?: string;
}

export interface MetricPayload {
  name: string;
  sql_expression: string;
  description?: string;
}

export interface SavedQuery {
  id: number;
  workspace_id: number;
  created_by: number;
  name: string;
  description?: string | null;
  prompt?: string | null;
  sql: string;
  tags?: string | null;
  is_template: boolean;
  status: 'draft' | 'submitted' | 'approved' | 'rejected' | 'archived';
  visibility: 'private' | 'workspace_shared';
  created_at: string;
  updated_at: string;
}

export interface SavedQueryPayload {
  name: string;
  sql: string;
  prompt?: string;
  description?: string;
  tags?: string;
  visibility?: 'private' | 'workspace_shared';
  is_template?: boolean;
}

export interface Report {
  id: number;
  workspace_id: number;
  database_id: number;
  saved_query_id: number;
  name: string;
  schedule_cron: string;
  delivery_config: Record<string, unknown>;
  is_enabled: boolean;
  last_ran_at?: string | null;
}

export interface ReportPayload {
  name: string;
  saved_query_id: number;
  database_id: number;
  schedule_cron: string;
  delivery_config: Record<string, unknown>;
  is_enabled: boolean;
}

export interface Policy {
  id: number;
  workspace_id: number;
  name: string;
  description?: string | null;
  priority: number;
  rules_json: Record<string, unknown>;
}

export interface PolicyPayload {
  name: string;
  description?: string;
  priority?: number;
  rules: Record<string, unknown>;
}

export interface SensitivityRule {
  id: number;
  workspace_id: number;
  table_name: string;
  column_name: string;
  label: string;
  masking_strategy: string;
  priority: number;
  restricted_roles: string[];
}

export interface SensitivityRulePayload {
  table_name: string;
  column_name: string;
  label?: string;
  masking_strategy?: string;
  priority?: number;
  restricted_roles?: string[];
}

export interface ApprovalRequest {
  id: number;
  workspace_id: number;
  requester_id: number;
  approver_id?: number | null;
  status: string;
  db_id: number;
  sql_query: string;
  original_prompt?: string | null;
  risk_score?: number | null;
  denial_reason?: string | null;
  created_at: string;
}

export interface AuditEvent {
  id: number;
  org_id?: number | null;
  workspace_id?: number | null;
  user_id?: number | null;
  event_type: string;
  request_id?: string | null;
  details?: Record<string, unknown>;
  hash?: string | null;
  previous_hash?: string | null;
  created_at: string;
}

export interface AuditLogResponse {
  events: AuditEvent[];
  total: number;
  skip: number;
  limit: number;
}

export interface AuditVerification {
  workspace_id: number;
  is_valid: boolean;
  timestamp: string;
}

export interface ConnectorHealth {
  id: number;
  db_name: string;
  status: string;
  last_check?: string | null;
  error?: string | null;
}
