import { PlannedFlow } from './api/models';
import { groupFlows } from './plan.store';

function flow(partial: Partial<PlannedFlow> & Pick<PlannedFlow, 'id' | 'name' | 'cadence'>): PlannedFlow {
  return {
    from_bucket_id: null,
    to_bucket_id: null,
    from_bucket_name: null,
    to_bucket_name: null,
    amount: '1.00',
    amount_rule: null,
    anchor_date: '2026-10-02',
    stop_rule: null,
    stop_date: null,
    redirect_to_bucket_id: null,
    redirect_to_bucket_name: null,
    match_pattern: null,
    active: true,
    created_at: '',
    updated_at: '',
    ...partial,
  };
}

describe('groupFlows', () => {
  it('orders groups per paycheck, weekly, monthly, annual and drops empty ones', () => {
    const groups = groupFlows([
      flow({ id: 1, name: 'Premium', cadence: 'annual_on_date' }),
      flow({ id: 2, name: 'Paycheck', cadence: 'per_paycheck' }),
      flow({ id: 3, name: 'Sweep', cadence: 'monthly_on_day' }),
    ]);
    expect(groups.map((g) => g.label)).toEqual(['Per paycheck', 'Monthly', 'Annual']);
  });

  it('sorts within a group by anchor date then name', () => {
    const [group] = groupFlows([
      flow({ id: 1, name: 'B', cadence: 'per_paycheck', anchor_date: '2026-10-02' }),
      flow({ id: 2, name: 'A', cadence: 'per_paycheck', anchor_date: '2026-10-02' }),
      flow({ id: 3, name: 'Earlier', cadence: 'per_paycheck', anchor_date: '2026-09-18' }),
    ]);
    expect(group.flows.map((f) => f.name)).toEqual(['Earlier', 'A', 'B']);
  });
});
