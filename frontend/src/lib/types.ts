export type EntityType = "LLC" | "Corp" | "LP" | "LLP" | "SoleProp" | "Nonprofit" | "Other";
export type CustomerType = "B2B" | "B2C" | "Government";
export type RevenueRange = "under_100k" | "100k_500k" | "500k_1m" | "1m_5m" | "5m_25m" | "over_25m";
export type TransactionRange = "under_200" | "200_1k" | "1k_10k" | "10k_100k" | "over_100k";
export type JobStatus = "queued" | "running" | "complete" | "failed";
export type StepStatus = "pending" | "running" | "complete" | "failed" | "skipped";

export interface IntakeForm {
  first_name: string;
  last_name: string;
  business_email: string;
  legal_name: string;
  domicile_state: string;
  entity_type: EntityType;
  employee_states: string[];
  business_nature: string;
  ecommerce_marketplace: boolean;
  customer_types: CustomerType[];
  product_service_location: string[];
  annual_revenue: RevenueRange;
  annual_transactions: TransactionRange;
  states_registered_sales_tax: string[];
}

export interface StepProgress {
  id: number;
  name: string;
  status: StepStatus;
  started_at: string | null;
  completed_at: string | null;
  error: string | null;
}

export interface AuditStatusResponse {
  job_id: string;
  status: JobStatus;
  created_at: string;
  updated_at: string;
  current_step: number;
  total_steps: number;
  progress_pct: number;
  steps: StepProgress[];
  eta_seconds: number | null;
}

export interface AuditSubmitResponse {
  job_id: string;
  status: JobStatus;
  status_url: string;
  message: string;
}

// ─── Report types ────────────────────────────────────────────────────────────

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type SectionStatus = "PASS" | "FAIL" | "WARNING" | "NOT_CHECKED";
export type SourceStatus = "checked" | "failed" | "skipped";
export type ActionUrgency = "critical" | "high" | "medium" | "low";

export interface ReportFinding {
  finding: string;
  source_field: string;
  source_name: string;
}

export interface ReportSection {
  section_id: string;
  title: string;
  status: SectionStatus;
  findings: ReportFinding[];
  recommendations: string[];
  sources: string[];
}

export interface ActionItem {
  priority: number; // 1–5
  action: string;
  urgency: ActionUrgency;
  estimated_cost: string | null;
}

export interface ReportSource {
  name: string;
  status: SourceStatus;
  checked_at: string | null;
}

export interface ScoreBreakdown {
  entity_status: number;
  federal_compliance: number;
  sanctions_watchlists: number;
  tax_exposure: number;
  license_status: number;
}

export interface ReportSchema {
  overall_risk_score: RiskLevel;
  score_breakdown: ScoreBreakdown;
  executive_summary: string;
  sections: ReportSection[];
  top_action_items: ActionItem[];
  data_sources_checked: ReportSource[];
  generated_at: string;
  disclaimer: string;
}

// ─── US States ───────────────────────────────────────────────────────────────

export const US_STATES: { code: string; name: string }[] = [
  { code: "AL", name: "Alabama" }, { code: "AK", name: "Alaska" },
  { code: "AZ", name: "Arizona" }, { code: "AR", name: "Arkansas" },
  { code: "CA", name: "California" }, { code: "CO", name: "Colorado" },
  { code: "CT", name: "Connecticut" }, { code: "DE", name: "Delaware" },
  { code: "DC", name: "District of Columbia" }, { code: "FL", name: "Florida" },
  { code: "GA", name: "Georgia" }, { code: "HI", name: "Hawaii" },
  { code: "ID", name: "Idaho" }, { code: "IL", name: "Illinois" },
  { code: "IN", name: "Indiana" }, { code: "IA", name: "Iowa" },
  { code: "KS", name: "Kansas" }, { code: "KY", name: "Kentucky" },
  { code: "LA", name: "Louisiana" }, { code: "ME", name: "Maine" },
  { code: "MD", name: "Maryland" }, { code: "MA", name: "Massachusetts" },
  { code: "MI", name: "Michigan" }, { code: "MN", name: "Minnesota" },
  { code: "MS", name: "Mississippi" }, { code: "MO", name: "Missouri" },
  { code: "MT", name: "Montana" }, { code: "NE", name: "Nebraska" },
  { code: "NV", name: "Nevada" }, { code: "NH", name: "New Hampshire" },
  { code: "NJ", name: "New Jersey" }, { code: "NM", name: "New Mexico" },
  { code: "NY", name: "New York" }, { code: "NC", name: "North Carolina" },
  { code: "ND", name: "North Dakota" }, { code: "OH", name: "Ohio" },
  { code: "OK", name: "Oklahoma" }, { code: "OR", name: "Oregon" },
  { code: "PA", name: "Pennsylvania" }, { code: "RI", name: "Rhode Island" },
  { code: "SC", name: "South Carolina" }, { code: "SD", name: "South Dakota" },
  { code: "TN", name: "Tennessee" }, { code: "TX", name: "Texas" },
  { code: "UT", name: "Utah" }, { code: "VT", name: "Vermont" },
  { code: "VA", name: "Virginia" }, { code: "WA", name: "Washington" },
  { code: "WV", name: "West Virginia" }, { code: "WI", name: "Wisconsin" },
  { code: "WY", name: "Wyoming" },
];
