// ===== SIIMS Frontend Type Definitions =====
// Mirrors the backend Pydantic schemas exactly.

// --- Enums (as string unions) ---
export type UserRole = 'system_admin' | 'ict_technician' | 'school_management';
export type ComputerStatus = 'online' | 'offline' | 'warning' | 'critical' | 'maintenance' | 'unknown';
export type IncidentSeverity = 'low' | 'medium' | 'high' | 'critical';
export type IncidentStatus = 'open' | 'in_progress' | 'resolved' | 'closed';
export type IncidentCategory = 'hardware' | 'software' | 'network' | 'security' | 'performance' | 'maintenance' | 'other';
export type UpdateType = 'comment' | 'status_change' | 'assignment' | 'resolution';
export type LicenceStatus = 'active' | 'expired' | 'expiring_soon' | 'perpetual' | 'unknown';
export type AlertSeverity = 'warning' | 'critical' | 'info';
export type AlertStatus = 'active' | 'acknowledged' | 'resolved';
export type AlertType =
  | 'cpu_high' | 'ram_high' | 'disk_high' | 'disk_critical' | 'smart_failure'
  | 'computer_offline' | 'network_issue' | 'licence_expiring' | 'licence_expired'
  | 'battery_low' | 'custom';
export type MaintenanceType = 'preventive' | 'corrective' | 'upgrade' | 'inspection' | 'other';
export type NotificationType = 'alert' | 'incident' | 'licence' | 'maintenance' | 'system' | 'info';
export type ReportFormat = 'pdf' | 'excel' | 'csv';
export type ReportType =
  | 'computers' | 'hardware' | 'network' | 'software' | 'licences' | 'incidents' | 'maintenance' | 'downtime';

// --- Auth ---
export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
export interface AccessTokenResponse {
  access_token: string;
  token_type: string;
}
export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

// --- Users ---
export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  phone: string | null;
  created_at: string;
  updated_at: string;
  last_login: string | null;
}
export interface UserCreate {
  email: string;
  full_name: string;
  password: string;
  role: UserRole;
  phone?: string;
}
export interface UserUpdate {
  full_name?: string;
  email?: string;
  role?: UserRole;
  phone?: string;
  is_active?: boolean;
}
export interface ResetPasswordResponse {
  temp_password: string;
  message: string;
}
export interface UserListResponse {
  items: User[];
  total: number;
  page: number;
  pages: number;
}

// --- Locations ---
export interface Location {
  id: number;
  name: string;
  description: string | null;
  building: string | null;
  floor: string | null;
  created_at: string;
  updated_at: string;
}
export interface LocationCreate {
  name: string;
  description?: string;
  building?: string;
  floor?: string;
}
export interface LocationUpdate extends Partial<LocationCreate> {}

// --- Computers ---
export interface Computer {
  id: number;
  hostname: string;
  ip_address: string | null;
  mac_address: string | null;
  manufacturer: string | null;
  model: string | null;
  processor: string | null;
  ram_gb: number | null;
  storage_gb: number | null;
  operating_system: string | null;
  os_version: string | null;
  location_id: number | null;
  department: string | null;
  is_active: boolean;
  status: ComputerStatus;
  notes: string | null;
  registered_at: string;
  last_seen: string | null;
  updated_at: string;
}
export interface ComputerCreate {
  hostname: string;
  ip_address?: string;
  mac_address?: string;
  manufacturer?: string;
  model?: string;
  processor?: string;
  ram_gb?: number;
  storage_gb?: number;
  operating_system?: string;
  os_version?: string;
  location_id?: number;
  department?: string;
  notes?: string;
}
export interface ComputerUpdate extends Partial<ComputerCreate> {
  is_active?: boolean;
}
export interface ComputerListResponse {
  items: Computer[];
  total: number;
  page: number;
  pages: number;
}
export interface AgentKeyResponse {
  computer_id: number;
  api_key: string;
  message: string;
}

// --- Hardware metrics ---
export interface HardwareMetric {
  id: number;
  computer_id: number;
  recorded_at: string;
  cpu_percent: number | null;
  cpu_freq_mhz: number | null;
  cpu_count_logical: number | null;
  cpu_temp_celsius: number | null;
  ram_total_gb: number | null;
  ram_used_gb: number | null;
  ram_percent: number | null;
  disk_total_gb: number | null;
  disk_used_gb: number | null;
  disk_free_gb: number | null;
  disk_percent: number | null;
  smart_status: string | null;
  uptime_seconds: number | null;
  battery_percent: number | null;
  battery_plugged: boolean | null;
}
export interface Threshold {
  cpu_warning_percent: number;
  ram_warning_percent: number;
  disk_warning_percent: number;
  disk_critical_percent: number;
  offline_timeout_minutes: number;
  heartbeat_interval_seconds: number;
  software_scan_interval_hours: number;
  data_retention_days: number;
}
export interface ThresholdUpdate extends Partial<Threshold> {}

// --- Network metrics ---
export interface NetworkMetric {
  id: number;
  computer_id: number;
  recorded_at: string;
  interface_name: string | null;
  ip_address: string | null;
  mac_address: string | null;
  is_up: boolean | null;
  gateway_reachable: boolean | null;
  dns_resolves: boolean | null;
  server_reachable: boolean | null;
  latency_ms: number | null;
  packet_loss_percent: number | null;
  bytes_sent: number | null;
  bytes_recv: number | null;
}

// --- Software ---
export interface InstalledSoftware {
  id: number;
  computer_id: number;
  name: string;
  version: string | null;
  publisher: string | null;
  install_date: string | null;
  first_seen: string;
  last_seen: string;
  is_active: boolean;
}
export interface SoftwareListResponse {
  items: InstalledSoftware[];
  total: number;
  page: number;
  pages: number;
}
export interface SoftwareSummaryItem {
  name: string;
  count: number;
  versions: string[];
}

// --- Licences ---
export interface SoftwareLicence {
  id: number;
  software_name: string;
  version: string | null;
  licence_type: string | null;
  vendor: string | null;
  seats: number | null;
  purchase_date: string | null;
  expiry_date: string | null;
  cost: number | null;
  notes: string | null;
  status: LicenceStatus;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  assignments_count: number | null;
}
export interface LicenceCreate {
  software_name: string;
  version?: string;
  licence_key?: string;
  licence_type?: string;
  vendor?: string;
  seats?: number;
  purchase_date?: string;
  expiry_date?: string;
  cost?: number;
  notes?: string;
}
export interface LicenceUpdate extends Partial<LicenceCreate> {
  is_active?: boolean;
}

// --- Incidents ---
export interface IncidentUpdate {
  id: number;
  incident_id: number;
  user_id: number | null;
  update_type: UpdateType;
  message: string;
  old_status: string | null;
  new_status: string | null;
  created_at: string;
}
export interface Incident {
  id: number;
  incident_number: string;
  computer_id: number | null;
  title: string;
  description: string | null;
  category: IncidentCategory;
  severity: IncidentSeverity;
  status: IncidentStatus;
  created_by_id: number | null;
  assigned_to_id: number | null;
  is_auto_created: boolean;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
  resolution_notes: string | null;
  updates: IncidentUpdate[];
}
export interface IncidentCreate {
  computer_id?: number;
  title: string;
  description?: string;
  category: IncidentCategory;
  severity: IncidentSeverity;
}
export interface IncidentUpdateSchema {
  title?: string;
  description?: string;
  category?: IncidentCategory;
  severity?: IncidentSeverity;
  status?: IncidentStatus;
}

// --- Maintenance ---
export interface MaintenanceRecord {
  id: number;
  computer_id: number;
  performed_by_id: number | null;
  maintenance_type: MaintenanceType;
  title: string;
  description: string | null;
  scheduled_date: string | null;
  completed_date: string | null;
  cost: number | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}
export interface MaintenanceCreate {
  computer_id: number;
  maintenance_type: MaintenanceType;
  title: string;
  description?: string;
  scheduled_date?: string;
  cost?: number;
  notes?: string;
}
export interface MaintenanceCompleteRequest {
  notes?: string;
  completed_date?: string;
}

// --- Alerts ---
export interface Alert {
  id: number;
  computer_id: number;
  alert_type: AlertType;
  severity: AlertSeverity;
  status: AlertStatus;
  title: string;
  message: string | null;
  metric_value: number | null;
  threshold_value: number | null;
  is_acknowledged: boolean;
  acknowledged_by_id: number | null;
  acknowledged_at: string | null;
  resolved_at: string | null;
  created_at: string;
  updated_at: string;
}

// --- Notifications ---
export interface Notification {
  id: number;
  user_id: number;
  title: string;
  message: string | null;
  notification_type: NotificationType;
  related_id: number | null;
  related_type: string | null;
  is_read: boolean;
  created_at: string;
  read_at: string | null;
}
export interface NotificationListResponse {
  items: Notification[];
  total: number;
  unread_count: number;
  page: number;
  pages: number;
}

// --- Settings ---
export interface SystemSetting {
  id: number;
  key: string;
  value: string | null;
  value_type: string;
  description: string | null;
  category: string | null;
  updated_at: string;
}
export interface SettingUpdate {
  key: string;
  value: string;
}
export interface EmailTestResponse {
  success: boolean;
  message: string;
}

// --- Audit ---
export interface AuditLog {
  id: number;
  user_id: number | null;
  action: string;
  entity_type: string | null;
  entity_id: number | null;
  details: unknown;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
}
export interface AuditLogListResponse {
  items: AuditLog[];
  total: number;
  page: number;
  pages: number;
}

// --- Generic pagination params ---
export interface PaginationParams {
  skip?: number;
  limit?: number;
}

// --- Dashboard (client-aggregated) ---
export interface DashboardStats {
  total_computers: number;
  online_computers: number;
  offline_computers: number;
  warning_computers: number;
  critical_computers: number;
  unknown_computers: number;
  active_alerts: number;
  open_incidents: number;
  expiring_licences: number;
  status_distribution: Array<{ name: string; value: number }>;
}

// --- Query param maps for list endpoints ---
export interface ComputerQueryParams {
  skip?: number;
  limit?: number;
  status?: ComputerStatus;
  location_id?: number;
  search?: string;
}
export interface IncidentQueryParams {
  skip?: number;
  limit?: number;
  status?: IncidentStatus;
  severity?: IncidentSeverity;
  computer_id?: number;
}
export interface SoftwareQueryParams {
  skip?: number;
  limit?: number;
  computer_id?: number;
  name?: string;
}
export interface AuditQueryParams {
  skip?: number;
  limit?: number;
  user_id?: number;
  entity_type?: string;
  action?: string;
  date_from?: string;
  date_to?: string;
}
export interface ReportFilters {
  date_from?: string;
  date_to?: string;
  location_id?: number;
  computer_id?: number;
}
