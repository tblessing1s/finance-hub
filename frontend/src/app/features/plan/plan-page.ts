import { Component, OnInit, computed, inject, signal } from '@angular/core';

import {
  AMOUNT_RULES,
  Bucket,
  BUCKET_KINDS,
  Cadence,
  PlannedFlow,
  labelFor,
} from '../../core/api/models';
import { formatMoney } from '../../core/money';
import { PlanStore } from '../../core/plan.store';
import { EmptyState } from '../../shared/ui/empty-state';
import { BucketFormSheet } from './bucket-form-sheet';
import { FlowFormSheet } from './flow-form-sheet';
import { FlowMap } from './flow-map';

type SheetState =
  | { kind: 'none' }
  | { kind: 'bucket'; bucket: Bucket | null }
  | { kind: 'flow'; flow: PlannedFlow | null; preset: Cadence | null };

/**
 * Plan: planned flows grouped by cadence, plus the buckets they move between.
 * Entry order the empty states steer toward: buckets with floors and targets, then paycheck
 * flows, then monthly and annual flows.
 */
@Component({
  selector: 'app-plan-page',
  imports: [EmptyState, BucketFormSheet, FlowFormSheet, FlowMap],
  templateUrl: './plan-page.html',
  styleUrl: './plan-page.scss',
})
export class PlanPage implements OnInit {
  protected readonly store = inject(PlanStore);
  protected readonly sheet = signal<SheetState>({ kind: 'none' });
  protected readonly bucketsOpen = signal(true);

  protected readonly fmt = formatMoney;
  protected readonly kindLabel = (b: Bucket) => labelFor(BUCKET_KINDS, b.kind);

  protected readonly bucketSheetOpen = computed(() => this.sheet().kind === 'bucket');
  protected readonly flowSheetOpen = computed(() => this.sheet().kind === 'flow');
  protected readonly editingBucket = computed(() => {
    const s = this.sheet();
    return s.kind === 'bucket' ? s.bucket : null;
  });
  protected readonly editingFlow = computed(() => {
    const s = this.sheet();
    return s.kind === 'flow' ? s.flow : null;
  });
  protected readonly presetCadence = computed(() => {
    const s = this.sheet();
    return s.kind === 'flow' ? s.preset : null;
  });

  /** Which step of the entry order the owner is on; drives the empty states. */
  protected readonly stage = computed<'loading' | 'error' | 'buckets' | 'paycheck' | 'ready'>(() => {
    if (this.store.error()) return 'error';
    if (!this.store.loaded()) return 'loading';
    if (!this.store.hasBuckets()) return 'buckets';
    if (!this.store.hasFlows()) return 'paycheck';
    return 'ready';
  });

  protected readonly hasPaycheckFlow = computed(() =>
    this.store.flows().some((f) => f.cadence === 'per_paycheck'),
  );

  ngOnInit(): void {
    void this.store.load();
  }

  protected addBucket(): void {
    this.sheet.set({ kind: 'bucket', bucket: null });
  }

  protected editBucket(bucket: Bucket): void {
    this.sheet.set({ kind: 'bucket', bucket });
  }

  protected editBucketById(id: number): void {
    const bucket = this.store.bucketsById().get(id);
    if (bucket) this.editBucket(bucket);
  }

  protected addFlow(preset: Cadence | null = null): void {
    this.sheet.set({ kind: 'flow', flow: null, preset });
  }

  protected editFlow(flow: PlannedFlow): void {
    this.sheet.set({ kind: 'flow', flow, preset: null });
  }

  protected closeSheet(): void {
    this.sheet.set({ kind: 'none' });
  }

  protected afterBucketSaved(): void {
    // Collapsing the bucket list once there are a few keeps flows above the fold on a phone.
    if (this.store.buckets().length >= 4) this.bucketsOpen.set(false);
  }

  /** "WF Checking → Schwab Hub", with the outside world named for one-ended flows. */
  protected route(f: PlannedFlow): string {
    const from = f.from_bucket_name ?? 'Income';
    const to = f.to_bucket_name ?? 'Outside';
    return `${from} → ${to}`;
  }

  protected amountLabel(f: PlannedFlow): string {
    return f.amount !== null ? formatMoney(f.amount) : labelFor(AMOUNT_RULES, f.amount_rule);
  }

  protected stopLabel(f: PlannedFlow): string {
    if (!f.stop_rule) return '';
    const redirect = f.redirect_to_bucket_name ? `, then → ${f.redirect_to_bucket_name}` : '';
    switch (f.stop_rule) {
      case 'bucket_reaches_target':
        return `until ${f.to_bucket_name ?? 'destination'} reaches target${redirect}`;
      case 'headroom_zero':
        return `until 7-pay headroom is zero${redirect}`;
      case 'date':
        return `until ${f.stop_date}${redirect}`;
    }
  }

  protected flowCountLabel(b: Bucket): string {
    const n = this.store.flowCountByBucket().get(b.id) ?? 0;
    return n === 1 ? '1 flow' : `${n} flows`;
  }

  protected bucketSub(b: Bucket): string {
    const parts = [this.kindLabel(b)];
    if (b.floor !== null) parts.push(`floor ${formatMoney(b.floor)}`);
    if (b.target !== null) parts.push(`target ${formatMoney(b.target)}`);
    return parts.join(' · ');
  }
}
