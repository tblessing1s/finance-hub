import { Injectable, computed, inject, signal } from '@angular/core';

import { BucketsService } from './api/buckets.service';
import { describeApiError } from './api/api-error';
import {
  Bucket,
  BucketInput,
  CADENCES,
  Cadence,
  PlannedFlow,
  PlannedFlowInput,
} from './api/models';
import { PlannedFlowsService } from './api/planned-flows.service';

export interface FlowGroup {
  cadence: Cadence;
  label: string;
  flows: PlannedFlow[];
}

/** Group flows by cadence in the Plan screen's display order; empty groups are dropped. */
export function groupFlows(flows: PlannedFlow[]): FlowGroup[] {
  return CADENCES.map(({ value, label }) => ({
    cadence: value,
    label,
    flows: flows
      .filter((f) => f.cadence === value)
      .sort((a, b) => a.anchor_date.localeCompare(b.anchor_date) || a.name.localeCompare(b.name)),
  })).filter((g) => g.flows.length > 0);
}

/** Signals-based state for buckets and planned flows. Mutations re-fetch the affected list. */
@Injectable({ providedIn: 'root' })
export class PlanStore {
  private readonly bucketsApi = inject(BucketsService);
  private readonly flowsApi = inject(PlannedFlowsService);

  readonly buckets = signal<Bucket[]>([]);
  readonly flows = signal<PlannedFlow[]>([]);
  readonly loading = signal(false);
  readonly loaded = signal(false);
  readonly error = signal<string | null>(null);

  readonly bucketsById = computed(() => new Map(this.buckets().map((b) => [b.id, b])));
  readonly groups = computed(() => groupFlows(this.flows()));
  readonly hasBuckets = computed(() => this.buckets().length > 0);
  readonly hasFlows = computed(() => this.flows().length > 0);
  readonly flowCountByBucket = computed(() => {
    const counts = new Map<number, number>();
    for (const f of this.flows()) {
      for (const id of [f.from_bucket_id, f.to_bucket_id]) {
        if (id !== null) counts.set(id, (counts.get(id) ?? 0) + 1);
      }
    }
    return counts;
  });

  async load(): Promise<void> {
    this.loading.set(true);
    this.error.set(null);
    try {
      const [buckets, flows] = await Promise.all([this.bucketsApi.list(), this.flowsApi.list()]);
      this.buckets.set(buckets);
      this.flows.set(flows);
      this.loaded.set(true);
    } catch (err) {
      this.error.set(describeApiError(err));
    } finally {
      this.loading.set(false);
    }
  }

  async saveBucket(id: number | null, input: BucketInput): Promise<Bucket> {
    const saved = id === null
      ? await this.bucketsApi.create(input)
      : await this.bucketsApi.update(id, input);
    await this.refreshBuckets();
    if (id !== null) await this.refreshFlows(); // bucket names are denormalized on flows
    return saved;
  }

  async deleteBucket(id: number): Promise<void> {
    await this.bucketsApi.remove(id);
    await this.refreshBuckets();
  }

  async saveFlow(id: number | null, input: PlannedFlowInput): Promise<PlannedFlow> {
    const saved = id === null
      ? await this.flowsApi.create(input)
      : await this.flowsApi.update(id, input);
    await this.refreshFlows();
    return saved;
  }

  async setFlowActive(id: number, active: boolean): Promise<void> {
    await this.flowsApi.update(id, { active });
    await this.refreshFlows();
  }

  async deleteFlow(id: number): Promise<void> {
    await this.flowsApi.remove(id);
    await this.refreshFlows();
  }

  private async refreshBuckets(): Promise<void> {
    this.buckets.set(await this.bucketsApi.list());
  }

  private async refreshFlows(): Promise<void> {
    this.flows.set(await this.flowsApi.list());
  }
}
