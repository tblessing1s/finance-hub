/**
 * Pure layout for the Plan flow map. Buckets are nodes in rows (layers) from income at the top
 * to outside bills at the bottom; flows are edges between them. No DOM, so it is unit-testable.
 */
import { Bucket, Cadence, PlannedFlow } from '../../core/api/models';
import { formatMoney } from '../../core/money';

/** Brief open item: confirm 26 vs 24 checks. One constant so the switch is a one-liner. */
export const PAYCHECKS_PER_YEAR = 26;

export const INCOME_ID = 'income';
export const OUTSIDE_ID = 'outside';

export interface MapNode {
  id: string; // bucket id as string, or INCOME_ID / OUTSIDE_ID
  bucketId: number | null;
  label: string;
  external: boolean;
  layer: number;
  x: number;
  y: number;
  w: number;
  h: number;
  netMonthly: number | null; // inflows − outflows per month across fixed-amount active flows
  hasRuleFlow: boolean; // a sweep/remainder touches it, so the net is a lower bound
}

export interface MapEdge {
  id: string;
  from: string;
  to: string;
  flowIds: number[];
  flow: PlannedFlow | null; // set when exactly one flow makes up the edge (tap opens it)
  label: string;
  monthly: number; // monthly-equivalent dollars for width; 0 for pure rule edges
  kind: 'fixed' | 'rule' | 'redirect';
  active: boolean;
  width: number;
  path: string;
  labelX: number;
  labelY: number;
}

export interface FlowMapLayout {
  width: number;
  height: number;
  nodes: MapNode[];
  edges: MapEdge[];
}

type Pt = [number, number];

export const MAP_WIDTH = 360;
const NODE_H = 44;
const ROW_GAP = 76;
const COL_GAP = 12;
const PAD = 8;
const MAX_NODE_W = 112;

export function monthlyMultiplier(cadence: Cadence): number {
  switch (cadence) {
    case 'per_paycheck':
      return PAYCHECKS_PER_YEAR / 12;
    case 'weekly':
      return 52 / 12;
    case 'monthly_on_day':
      return 1;
    case 'annual_on_date':
      return 1 / 12;
  }
}

export function cadenceSuffix(cadence: Cadence): string {
  switch (cadence) {
    case 'per_paycheck':
      return '/check';
    case 'weekly':
      return '/wk';
    case 'monthly_on_day':
      return '/mo';
    case 'annual_on_date':
      return '/yr';
  }
}

export function monthlyAmount(f: PlannedFlow): number {
  return f.amount === null ? 0 : Number(f.amount) * monthlyMultiplier(f.cadence);
}

function nodeKey(bucketId: number | null, side: 'from' | 'to'): string {
  if (bucketId !== null) return String(bucketId);
  return side === 'from' ? INCOME_ID : OUTSIDE_ID;
}

function ruleShort(f: PlannedFlow): string {
  return f.amount_rule === 'sweep_above_floor' ? 'sweep above floor' : 'remainder';
}

/** Longest-path layering with cycle breaking. Income is layer 0 when present. */
function assignLayers(nodeIds: string[], edges: { from: string; to: string }[]): Map<string, number> {
  const preds = new Map<string, Set<string>>(nodeIds.map((id) => [id, new Set()]));
  const succs = new Map<string, Set<string>>(nodeIds.map((id) => [id, new Set()]));
  for (const e of edges) {
    if (e.from === e.to) continue;
    preds.get(e.to)!.add(e.from);
    succs.get(e.from)!.add(e.to);
  }
  const layer = new Map<string, number>();
  const remaining = new Set(nodeIds);
  const indeg = new Map(nodeIds.map((id) => [id, preds.get(id)!.size]));
  while (remaining.size) {
    let ready = [...remaining].filter((id) => indeg.get(id) === 0);
    if (!ready.length) {
      // Cycle: force the node with the fewest unresolved predecessors.
      ready = [[...remaining].sort((a, b) => indeg.get(a)! - indeg.get(b)!)[0]];
    }
    for (const id of ready) {
      const resolved = [...preds.get(id)!].filter((p) => layer.has(p)).map((p) => layer.get(p)!);
      layer.set(id, resolved.length ? Math.max(...resolved) + 1 : 0);
      remaining.delete(id);
      for (const s of succs.get(id)!) indeg.set(s, indeg.get(s)! - 1);
    }
  }
  return layer;
}

export function layoutFlowMap(buckets: Bucket[], flows: PlannedFlow[]): FlowMapLayout {
  const active = flows.filter((f) => f.active);
  const hasIncome = flows.some((f) => f.from_bucket_id === null);
  const hasOutside = flows.some((f) => f.to_bucket_id === null);

  // Nodes: only buckets that take part in a flow, plus the two external endpoints.
  const touched = new Set<number>();
  for (const f of flows) {
    for (const id of [f.from_bucket_id, f.to_bucket_id, f.redirect_to_bucket_id]) {
      if (id !== null) touched.add(id);
    }
  }
  const bucketById = new Map(buckets.map((b) => [b.id, b]));
  const nodeIds: string[] = [];
  if (hasIncome) nodeIds.push(INCOME_ID);
  for (const id of touched) if (bucketById.has(id)) nodeIds.push(String(id));
  if (hasOutside) nodeIds.push(OUTSIDE_ID);

  // Edges aggregated per (from, to); redirects are their own dotted edge.
  const groups = new Map<string, PlannedFlow[]>();
  for (const f of flows) {
    const key = `${nodeKey(f.from_bucket_id, 'from')}>${nodeKey(f.to_bucket_id, 'to')}`;
    groups.set(key, [...(groups.get(key) ?? []), f]);
  }
  const edges: MapEdge[] = [];
  for (const [key, fs] of groups) {
    const [from, to] = key.split('>');
    const monthly = fs.filter((f) => f.active).reduce((s, f) => s + monthlyAmount(f), 0);
    const allRule = fs.every((f) => f.amount === null);
    const label =
      fs.length === 1
        ? fs[0].amount !== null
          ? `${formatMoney(fs[0].amount)}${cadenceSuffix(fs[0].cadence)}`
          : ruleShort(fs[0])
        : allRule
          ? `${fs.length} rules`
          : `${formatMoney(Math.round(monthly))}/mo · ${fs.length} flows`;
    edges.push({
      id: key,
      from,
      to,
      flowIds: fs.map((f) => f.id),
      flow: fs.length === 1 ? fs[0] : null,
      label,
      monthly,
      kind: allRule ? 'rule' : 'fixed',
      active: fs.some((f) => f.active),
      width: 0,
      path: '',
      labelX: 0,
      labelY: 0,
    });
  }
  for (const f of flows) {
    if (f.redirect_to_bucket_id === null || !bucketById.has(f.redirect_to_bucket_id)) continue;
    const from = nodeKey(f.from_bucket_id, 'from');
    const to = String(f.redirect_to_bucket_id);
    if (from === to) continue;
    const amount = f.amount !== null ? formatMoney(f.amount) + cadenceSuffix(f.cadence) : ruleShort(f);
    edges.push({
      id: `redirect:${f.id}`,
      from,
      to,
      flowIds: [f.id],
      flow: f,
      label: `${amount} after ${f.to_bucket_name ?? 'target'} fills`,
      monthly: 0,
      kind: 'redirect',
      active: f.active,
      width: 0,
      path: '',
      labelX: 0,
      labelY: 0,
    });
  }

  // Layers from every edge, redirects included: a redirect target sits below its source.
  const layer = assignLayers(nodeIds, edges);
  if (hasOutside) {
    const maxBucketLayer = Math.max(0, ...nodeIds.filter((id) => id !== OUTSIDE_ID).map((id) => layer.get(id)!));
    layer.set(OUTSIDE_ID, maxBucketLayer + 1);
  }

  // Net per month per bucket (fixed-amount active flows only).
  const net = new Map<string, number>();
  const ruleTouch = new Set<string>();
  for (const f of active) {
    const from = nodeKey(f.from_bucket_id, 'from');
    const to = nodeKey(f.to_bucket_id, 'to');
    if (f.amount === null) {
      ruleTouch.add(from);
      ruleTouch.add(to);
      continue;
    }
    const m = monthlyAmount(f);
    net.set(from, (net.get(from) ?? 0) - m);
    net.set(to, (net.get(to) ?? 0) + m);
  }

  // Place rows.
  const rows = new Map<number, string[]>();
  for (const id of nodeIds) {
    const l = layer.get(id)!;
    rows.set(l, [...(rows.get(l) ?? []), id]);
  }
  const nodes: MapNode[] = [];
  const pos = new Map<string, MapNode>();
  const layerCount = rows.size ? Math.max(...rows.keys()) + 1 : 0;
  for (let l = 0; l < layerCount; l++) {
    const ids = (rows.get(l) ?? []).sort((a, b) => sortKey(a, bucketById).localeCompare(sortKey(b, bucketById)));
    if (!ids.length) continue;
    const n = ids.length;
    const w = Math.min(MAX_NODE_W, (MAP_WIDTH - 2 * PAD - COL_GAP * (n - 1)) / n);
    const totalW = n * w + (n - 1) * COL_GAP;
    const x0 = (MAP_WIDTH - totalW) / 2;
    ids.forEach((id, i) => {
      const external = id === INCOME_ID || id === OUTSIDE_ID;
      const bucketId = external ? null : Number(id);
      const node: MapNode = {
        id,
        bucketId,
        label: external ? (id === INCOME_ID ? 'Income' : 'Outside') : bucketById.get(bucketId!)!.name,
        external,
        layer: l,
        x: x0 + i * (w + COL_GAP),
        y: PAD + l * (NODE_H + ROW_GAP),
        w,
        h: NODE_H,
        netMonthly: external ? null : (net.get(id) ?? 0),
        hasRuleFlow: ruleTouch.has(id),
      };
      nodes.push(node);
      pos.set(id, node);
    });
  }

  // Edge geometry. Width from monthly volume on a sqrt scale so one big flow doesn't flatten the rest.
  const maxMonthly = Math.max(1, ...edges.map((e) => e.monthly));
  const placed = edges.filter((e) => pos.has(e.from) && pos.has(e.to));
  const centerX = (id: string) => pos.get(id)!.x + pos.get(id)!.w / 2;
  const slots = (key: 'from' | 'to', other: 'from' | 'to') => {
    const byNode = new Map<string, MapEdge[]>();
    for (const e of placed) byNode.set(e[key], [...(byNode.get(e[key]) ?? []), e]);
    const slot = new Map<string, { i: number; n: number }>();
    for (const [, es] of byNode) {
      es.sort((a, b) => centerX(a[other]) - centerX(b[other]));
      es.forEach((e, i) => slot.set(e.id, { i, n: es.length }));
    }
    return slot;
  };
  const outSlot = slots('from', 'to');
  const inSlot = slots('to', 'from');
  // Free x positions per row (between nodes and in the margins), for routing long edges around.
  const rowGaps = new Map<number, number[]>();
  for (const [l, ids] of rows) {
    const spans = ids.map((id) => pos.get(id)!).sort((a, b) => a.x - b.x);
    const gaps: number[] = [];
    if (spans[0].x > 40) gaps.push(spans[0].x / 2);
    for (let k = 0; k + 1 < spans.length; k++) gaps.push((spans[k].x + spans[k].w + spans[k + 1].x) / 2);
    const last = spans[spans.length - 1];
    if (MAP_WIDTH - (last.x + last.w) > 40) gaps.push((last.x + last.w + MAP_WIDTH) / 2);
    rowGaps.set(l, gaps.length ? gaps : [MAP_WIDTH / 2]);
  }
  const rowCenterY = (l: number) => PAD + l * (NODE_H + ROW_GAP) + NODE_H / 2;

  for (const e of placed) {
    const a = pos.get(e.from)!;
    const b = pos.get(e.to)!;
    const o = outSlot.get(e.id)!;
    const i = inSlot.get(e.id)!;
    const sx = a.x + (a.w * (o.i + 1)) / (o.n + 1);
    const tx = b.x + (b.w * (i.i + 1)) / (i.n + 1);
    e.width = e.kind === 'redirect' ? 1.5 : 1.5 + 8 * Math.sqrt(e.monthly / maxMonthly);
    const halfLabel = Math.min(e.label.length * 2.9, MAP_WIDTH / 2 - PAD);
    if (b.layer > a.layer) {
      const sy = a.y + a.h;
      const ty = b.y;
      // Waypoints through the nearest free gap of every row the edge crosses.
      const pts: Pt[] = [[sx, sy]];
      let cx = sx;
      for (let l = a.layer + 1; l < b.layer; l++) {
        const gaps = rowGaps.get(l) ?? [MAP_WIDTH / 2];
        cx = gaps.reduce((best, g) => (Math.abs(g - cx) < Math.abs(best - cx) ? g : best), gaps[0]);
        pts.push([cx, rowCenterY(l)]);
      }
      pts.push([tx, ty]);
      e.path = pts
        .map((pt, k) => {
          if (k === 0) return `M${pt[0]},${pt[1]}`;
          const prev = pts[k - 1];
          const dy = (pt[1] - prev[1]) / 2;
          return `C${prev[0]},${prev[1] + dy} ${pt[0]},${pt[1] - dy} ${pt[0]},${pt[1]}`;
        })
        .join(' ');
      // Label in the first row gap below the source, spread by fan-out slot so siblings don't stack.
      const frac = o.n === 1 ? 0.5 : 0.22 + (0.56 * o.i) / (o.n - 1);
      const first = pts[1];
      const dy = (first[1] - sy) / 2;
      const pt = pointOnCubic([sx, sy], [sx, sy + dy], [first[0], first[1] - dy], first, sy + ROW_GAP * frac);
      e.labelX = Math.min(Math.max(pt[0], halfLabel), MAP_WIDTH - halfLabel);
      e.labelY = pt[1];
    } else {
      // Upward or same-row edge: loop out the right-hand side.
      const sy = a.y + a.h / 2;
      const ty = b.y + b.h / 2;
      const sx2 = a.x + a.w;
      const tx2 = b.x + b.w;
      const bulge = Math.min(Math.max(sx2, tx2) + 28, MAP_WIDTH - 4);
      e.path = `M${sx2},${sy} C${bulge},${sy} ${bulge},${ty} ${tx2},${ty}`;
      e.labelX = Math.min(bulge - 4, MAP_WIDTH - halfLabel);
      e.labelY = (sy + ty) / 2;
    }
  }

  const height = layerCount ? PAD * 2 + layerCount * NODE_H + (layerCount - 1) * ROW_GAP + 14 : 0;
  return { width: MAP_WIDTH, height, nodes, edges };
}

function sortKey(id: string, bucketById: Map<number, Bucket>): string {
  if (id === INCOME_ID) return '0';
  if (id === OUTSIDE_ID) return '~';
  return bucketById.get(Number(id))?.name ?? id;
}

export function formatNet(n: number | null, lowerBound: boolean): string {
  if (n === null) return '';
  const rounded = Math.round(n);
  const sign = rounded > 0 ? '+' : rounded < 0 ? '−' : '';
  return `${sign}${formatMoney(Math.abs(rounded))}/mo${lowerBound ? '*' : ''}`;
}


/** Point on a cubic Bézier whose y is closest to `targetY` (sampled; plenty for label placement). */
function pointOnCubic(p0: Pt, p1: Pt, p2: Pt, p3: Pt, targetY: number): Pt {
  let best: Pt = p0;
  let bestDist = Infinity;
  for (let k = 0; k <= 40; k++) {
    const t = k / 40;
    const u = 1 - t;
    const x = u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0];
    const y = u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1];
    const d = Math.abs(y - targetY);
    if (d < bestDist) {
      bestDist = d;
      best = [x, y];
    }
  }
  return best;
}
