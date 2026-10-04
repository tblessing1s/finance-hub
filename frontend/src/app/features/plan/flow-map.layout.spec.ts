import { Bucket, PlannedFlow } from '../../core/api/models';
import { INCOME_ID, OUTSIDE_ID, layoutFlowMap, monthlyAmount } from './flow-map.layout';

const bucket = (id: number, name: string): Bucket => ({
  id,
  name,
  kind: 'hub',
  floor: null,
  target: null,
  balance_source: 'manual',
  growth_rate_pct: null,
  created_at: '',
  updated_at: '',
});

const flow = (p: Partial<PlannedFlow> & Pick<PlannedFlow, 'id' | 'name'>): PlannedFlow => ({
  from_bucket_id: null,
  to_bucket_id: null,
  from_bucket_name: null,
  to_bucket_name: null,
  amount: '100.00',
  amount_rule: null,
  cadence: 'monthly_on_day',
  anchor_date: '2026-10-01',
  stop_rule: null,
  stop_date: null,
  redirect_to_bucket_id: null,
  redirect_to_bucket_name: null,
  match_pattern: null,
  active: true,
  created_at: '',
  updated_at: '',
  ...p,
});

const checking = bucket(1, 'WF Checking');
const hub = bucket(2, 'Schwab Hub');
const runway = bucket(3, 'Runway');
const engine = bucket(4, 'Engine');
const idle = bucket(5, 'Roth');

describe('monthlyAmount', () => {
  it('normalizes each cadence to dollars per month', () => {
    expect(monthlyAmount(flow({ id: 1, name: 'a', amount: '1200', cadence: 'per_paycheck' }))).toBeCloseTo(2600);
    expect(monthlyAmount(flow({ id: 1, name: 'a', amount: '120', cadence: 'annual_on_date' }))).toBeCloseTo(10);
    expect(monthlyAmount(flow({ id: 1, name: 'a', amount: '12', cadence: 'weekly' }))).toBeCloseTo(52);
    expect(monthlyAmount(flow({ id: 1, name: 'a', amount: null, amount_rule: 'remainder' }))).toBe(0);
  });
});

describe('layoutFlowMap', () => {
  const flows = [
    flow({ id: 1, name: 'Paycheck', to_bucket_id: 1, amount: '3200', cadence: 'per_paycheck' }),
    flow({ id: 2, name: 'Runway', from_bucket_id: 1, to_bucket_id: 3, amount: '500', cadence: 'per_paycheck', stop_rule: 'bucket_reaches_target', redirect_to_bucket_id: 4 }),
    flow({ id: 3, name: 'Sweep', from_bucket_id: 1, to_bucket_id: 2, amount: null, amount_rule: 'sweep_above_floor' }),
    flow({ id: 4, name: 'Premium', from_bucket_id: 1, amount: '15000', cadence: 'annual_on_date' }),
  ];
  const layout = layoutFlowMap([checking, hub, runway, engine, idle], flows);
  const byId = new Map(layout.nodes.map((n) => [n.id, n]));

  it('layers income above checking above its destinations above outside', () => {
    expect(byId.get(INCOME_ID)!.layer).toBe(0);
    expect(byId.get('1')!.layer).toBe(1);
    expect(byId.get('2')!.layer).toBe(2);
    expect(byId.get('3')!.layer).toBe(2);
    expect(byId.get('4')!.layer).toBe(2); // redirect target sits below its source
    expect(byId.get(OUTSIDE_ID)!.layer).toBe(3);
  });

  it('leaves out buckets no flow touches', () => {
    expect(byId.has('5')).toBe(false);
  });

  it('draws one edge per bucket pair plus a dotted redirect edge', () => {
    const kinds = layout.edges.map((e) => `${e.from}>${e.to}:${e.kind}`).sort();
    expect(kinds).toEqual(['1>2:rule', '1>3:fixed', '1>4:redirect', '1>outside:fixed', 'income>1:fixed'].sort());
  });

  it('labels edges with amount and cadence and scales width by monthly volume', () => {
    const pay = layout.edges.find((e) => e.id === 'income>1')!;
    const premium = layout.edges.find((e) => e.id === '1>outside')!;
    expect(pay.label).toBe('$3,200/check');
    expect(premium.label).toBe('$15,000/yr');
    expect(pay.width).toBeGreaterThan(premium.width);
    expect(layout.edges.find((e) => e.kind === 'rule')!.label).toBe('sweep above floor');
  });

  it('computes net per month on buckets from fixed flows and flags rule exposure', () => {
    const c = byId.get('1')!;
    // +3200*26/12 − 500*26/12 − 15000/12
    expect(c.netMonthly).toBeCloseTo((3200 - 500) * (26 / 12) - 1250, 5);
    expect(c.hasRuleFlow).toBe(true);
    expect(byId.get('4')!.netMonthly).toBe(0);
  });

  it('keeps every edge label inside the viewBox', () => {
    for (const e of layout.edges) {
      expect(e.labelX).toBeGreaterThan(0);
      expect(e.labelX).toBeLessThan(layout.width);
    }
  });

  it('routes a two-row edge around the middle row instead of through a node', () => {
    const premium = layout.edges.find((e) => e.id === '1>outside')!;
    const middle = layout.nodes.filter((n) => n.layer === 2);
    const midY = middle[0].y + middle[0].h / 2;
    // The path's waypoint at the middle row's y must not be inside any middle-row node.
    const m = premium.path.match(/C[^C]*?([\d.]+),([\d.]+)(?= C)/);
    expect(m).not.toBeNull();
    const [wx, wy] = [Number(m![1]), Number(m![2])];
    expect(wy).toBeCloseTo(midY, 3);
    expect(middle.some((n) => wx >= n.x && wx <= n.x + n.w)).toBe(false);
  });

  it('keeps every node inside the viewBox', () => {
    for (const n of layout.nodes) {
      expect(n.x).toBeGreaterThanOrEqual(0);
      expect(n.x + n.w).toBeLessThanOrEqual(layout.width);
      expect(n.y + n.h).toBeLessThanOrEqual(layout.height);
    }
  });

  it('survives a cycle between two buckets', () => {
    const cyc = layoutFlowMap([checking, hub], [
      flow({ id: 1, name: 'a', from_bucket_id: 1, to_bucket_id: 2 }),
      flow({ id: 2, name: 'b', from_bucket_id: 2, to_bucket_id: 1 }),
    ]);
    expect(cyc.nodes.length).toBe(2);
    expect(cyc.edges.every((e) => e.path.startsWith('M'))).toBe(true);
  });
});
