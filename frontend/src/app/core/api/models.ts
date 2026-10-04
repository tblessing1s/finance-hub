/** Mirrors backend/app/schemas. Money fields are decimal strings ("7500.00"), never floats. */

export type BucketKind =
  | 'checking'
  | 'hub'
  | 'policy_cv'
  | 'policy_loan'
  | 'runway'
  | 'lumpy_reserve'
  | 'engine'
  | 'roth'
  | 'ira'
  | 'k401';

export type BalanceSource = 'manual' | 'dashboard' | 'derived';
export type AmountRule = 'sweep_above_floor' | 'remainder';
export type Cadence = 'per_paycheck' | 'weekly' | 'monthly_on_day' | 'annual_on_date';
export type StopRule = 'bucket_reaches_target' | 'headroom_zero' | 'date';

export interface Bucket {
  id: number;
  name: string;
  kind: BucketKind;
  floor: string | null;
  target: string | null;
  balance_source: BalanceSource;
  growth_rate_pct: string | null;
  created_at: string;
  updated_at: string;
}

export type BucketInput = Omit<Bucket, 'id' | 'created_at' | 'updated_at'>;

export interface PlannedFlow {
  id: number;
  name: string;
  from_bucket_id: number | null;
  to_bucket_id: number | null;
  from_bucket_name: string | null;
  to_bucket_name: string | null;
  amount: string | null;
  amount_rule: AmountRule | null;
  cadence: Cadence;
  anchor_date: string;
  stop_rule: StopRule | null;
  stop_date: string | null;
  redirect_to_bucket_id: number | null;
  redirect_to_bucket_name: string | null;
  match_pattern: string | null;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export type PlannedFlowInput = Omit<
  PlannedFlow,
  'id' | 'created_at' | 'updated_at' | 'from_bucket_name' | 'to_bucket_name' | 'redirect_to_bucket_name'
>;

export const BUCKET_KINDS: { value: BucketKind; label: string }[] = [
  { value: 'checking', label: 'Checking' },
  { value: 'hub', label: 'Hub (Schwab)' },
  { value: 'policy_cv', label: 'Policy cash value' },
  { value: 'policy_loan', label: 'Policy loan' },
  { value: 'runway', label: 'Runway' },
  { value: 'lumpy_reserve', label: 'Lumpy reserve' },
  { value: 'engine', label: 'Engine (brokerage)' },
  { value: 'roth', label: 'Roth' },
  { value: 'ira', label: 'IRA' },
  { value: 'k401', label: '401k' },
];

export const BALANCE_SOURCES: { value: BalanceSource; label: string }[] = [
  { value: 'manual', label: 'Entered by hand' },
  { value: 'dashboard', label: 'Pulled from Rotation Dashboard' },
  { value: 'derived', label: 'Derived from other buckets' },
];

/** Display order for the Plan screen groups. */
export const CADENCES: { value: Cadence; label: string; anchorLabel: string }[] = [
  { value: 'per_paycheck', label: 'Per paycheck', anchorLabel: 'First paycheck date' },
  { value: 'weekly', label: 'Weekly', anchorLabel: 'First week (any date in it)' },
  { value: 'monthly_on_day', label: 'Monthly', anchorLabel: 'First date (sets the day of month)' },
  { value: 'annual_on_date', label: 'Annual', anchorLabel: 'First date (sets the day each year)' },
];

export const AMOUNT_RULES: { value: AmountRule; label: string }[] = [
  { value: 'sweep_above_floor', label: 'Sweep everything above the floor' },
  { value: 'remainder', label: 'Remainder after other flows' },
];

export const STOP_RULES: { value: StopRule; label: string }[] = [
  { value: 'bucket_reaches_target', label: 'When the destination reaches its target' },
  { value: 'headroom_zero', label: 'When 7-pay headroom hits zero' },
  { value: 'date', label: 'On a date' },
];

export function labelFor<T extends string>(
  list: { value: T; label: string }[],
  value: T | null | undefined,
): string {
  return list.find((x) => x.value === value)?.label ?? String(value ?? '');
}
