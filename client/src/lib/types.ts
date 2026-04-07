export type ProviderType = 'gemini' | 'local';

export interface UserDatabaseCreate {
  host: string;
  port: string;
  db_user: string;
  db_password: string;
  db_name: string;
}

export interface UserDatabase {
  id: number;
  user_id: number;
  host: string | null;
  port: number | null;
  db_user: string | null;
  db_name: string;
  mcp_api_key?: string;
  created_at: string;
}

export interface QueryHistoryItem {
  id: number;
  user_database_id: number;
  event_type: string;
  original_prompt: string | null;
  generated_sql: string | null;
  executed_sql: string | null;
  success: boolean;
  error_message: string | null;
  executed_at: string;
}

export interface GenerateSqlRequest {
  prompt: string;
  db_id: number;
  provider_type?: ProviderType;
  model_name?: string;
}

export interface GenerateSqlResponse {
  raw_sql: string;
  confirmation_required: boolean;
  message?: string | null;
}

export interface ExecuteSqlRequest {
  raw_sql: string;
  db_id: number;
  original_prompt?: string;
  generated_sql?: string;
}

export interface ExecuteSqlResponse {
  status: string;
  result?: Record<string, unknown>[] | null;
  error?: string | null;
}

export interface ExplainSqlResponse {
  status: string;
  result?: Record<string, unknown>[] | null;
}

export interface SchemaTableColumn {
  name: string;
  type: string;
  nullable: boolean;
  primary_key: boolean;
  comment?: string | null;
}

export interface SchemaForeignKey {
  constrained_columns?: string[];
  referred_schema?: string;
  referred_table: string;
  referred_columns?: string[];
}

export interface SchemaTableStructure {
  schema: string;
  table_name: string;
  columns: SchemaTableColumn[];
  foreign_keys: SchemaForeignKey[];
  indexes: Record<string, unknown>[];
}

export interface SchemaTableData {
  structure?: SchemaTableStructure;
  sample_data?: Record<string, string | null>[];
  error?: string;
}

export interface SchemaVisualization {
  schemas: string[];
  tables: Record<string, SchemaTableData>;
}
