export type DashboardMetrics = {
  total_revenue: number;
  revenue_at_risk: number;
  recoverable_revenue: number;
  recovered_revenue: number;
  recovery_rate: number;
  recovery_confidence: number;
  opportunity_count: number;
  pending_approvals: number;
  auto_approved_count: number;
  transaction_count: number;
  failed_count: number;
  customer_count: number;
  razorpay_mode: string;
  ai_mode: string;
};

export type TrendPoint = { date: string; captured: number; failed: number; recovered: number };
export type FailureBreakdown = { reason: string; count: number; amount: number };
export type TopCustomer = {
  id: number;
  name: string;
  email: string;
  expected_recovery: number;
  estimated_recovery_cost: number;
  expected_net_recovery: number;
  recovery_roi: number;
  recovery_strategy?: string | null;
  failed_amount: number;
  recovery_score: number;
};

export type AgentAction = {
  id: number;
  opportunity_id?: number | null;
  agent_name: string;
  action: string;
  decision: string;
  risk_level: string;
  reason: string;
  created_at: string;
};

export type Opportunity = {
  id: number;
  transaction_id: number;
  customer_id: number;
  amount: number;
  recovery_probability: number;
  expected_recovery: number;
  estimated_recovery_cost: number;
  expected_net_recovery: number;
  recovery_roi: number;
  recovery_strategy?: string | null;
  priority: string;
  reason: string;
  recommended_action: string;
  status: string;
  created_at: string;
  why_customer?: string | null;
  why_recover?: string | null;
  why_action?: string | null;
  risk_level?: string | null;
  customer_message?: string | null;
  ai_source?: string | null;
  customer_name?: string | null;
  customer_email?: string | null;
  failure_reason?: string | null;
  payment_method?: string | null;
  transaction_status?: string | null;
};

export type Transaction = {
  id: number;
  external_transaction_id: string;
  customer_id: number;
  amount: number;
  currency: string;
  status: string;
  payment_method: string;
  failure_reason?: string | null;
  created_at: string;
  recovered: boolean;
  recovery_probability?: number | null;
  recommended_action?: string | null;
  customer_name?: string | null;
  customer_email?: string | null;
};

export type Customer = {
  id: number;
  external_customer_id: string;
  name: string;
  email: string;
  phone: string;
  total_paid: number;
  successful_payments: number;
  failed_payments: number;
  average_transaction_value: number;
  lifetime_value: number;
  recovery_score: number;
};

export type PaymentLink = {
  id: number;
  opportunity_id: number;
  razorpay_link_id?: string | null;
  short_url: string;
  amount: number;
  status: string;
  created_at: string;
  reference_id: string;
  mode: string;
};

export type DashboardResponse = {
  metrics: DashboardMetrics;
  trend: TrendPoint[];
  failure_breakdown: FailureBreakdown[];
  recent_actions: AgentAction[];
  top_customers: TopCustomer[];
  opportunities: Opportunity[];
};

export type ExecuteResponse = {
  ok: boolean;
  message: string;
  requires_approval: boolean;
  auto_approved: boolean;
  opportunity?: Opportunity;
  payment_link?: PaymentLink | null;
  analysis?: RecoveryAnalysis | null;
  demo_mode: boolean;
  razorpay_mode: string;
};

export type GuardDecision = {
  allowed: boolean;
  requires_approval: boolean;
  auto_approved: boolean;
  risk_level: string;
  reasons: string[];
  policy_label: string;
};

export type RecoveryAnalysis = {
  decision: string;
  recommended_action: string;
  recovery_probability: number;
  expected_recovery: number;
  estimated_recovery_cost: number;
  expected_net_recovery: number;
  recovery_roi: number;
  recovery_strategy?: string | null;
  risk_level: string;
  reason: string;
  customer_message: string;
  why_customer: string;
  why_recover: string;
  why_action: string;
  ai_source: string;
  guard: GuardDecision;
};

export type AppSettings = {
  razorpay_mode: string;
  razorpay_configured: boolean;
  ai_mode: string;
  openai_configured: boolean;
  autonomous_amount_limit: number;
  webhook_configured: boolean;
  frontend_url: string;
  autonomous_enabled?: boolean;
};


export type SimulatorResponse = { limit: number; current_limit: number; autonomous_count: number; approval_count: number; expected_recovery: number; additional_expected_recovery: number };
