import { Component, computed, effect, inject, input, output, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { describeApiError } from '../../core/api/api-error';
import {
  BALANCE_SOURCES,
  BUCKET_KINDS,
  BalanceSource,
  Bucket,
  BucketInput,
  BucketKind,
} from '../../core/api/models';
import { fromApiMoney, toApiMoney } from '../../core/money';
import { PlanStore } from '../../core/plan.store';
import { Sheet } from '../../shared/ui/sheet';

/** Add or edit a bucket. Pass `bucket` to edit; null adds. */
@Component({
  selector: 'app-bucket-form-sheet',
  imports: [ReactiveFormsModule, Sheet],
  template: `
    <app-sheet [open]="open()" [title]="bucket() ? 'Edit bucket' : 'New bucket'" (closed)="closed.emit()">
      <form [formGroup]="form" (ngSubmit)="submit()" novalidate>
        @if (error()) {
          <p class="form-error" role="alert">{{ error() }}</p>
        }

        <div class="field" [class.invalid]="showError('name')">
          <label for="b-name">Name</label>
          <input id="b-name" formControlName="name" placeholder="WF Checking" autocomplete="off" />
        </div>

        <div class="field">
          <label for="b-kind">Kind</label>
          <select id="b-kind" formControlName="kind">
            @for (k of kinds; track k.value) {
              <option [value]="k.value">{{ k.label }}</option>
            }
          </select>
          <span class="hint">{{ kindHint() }}</span>
        </div>

        <div class="field-row">
          <div class="field" [class.invalid]="showError('floor')">
            <label for="b-floor">Floor ($)</label>
            <input id="b-floor" type="number" inputmode="decimal" min="0" step="0.01" formControlName="floor" placeholder="7500" />
            <span class="hint">Never swept below</span>
          </div>
          <div class="field" [class.invalid]="showError('target')">
            <label for="b-target">Target ($)</label>
            <input id="b-target" type="number" inputmode="decimal" min="0" step="0.01" formControlName="target" placeholder="30000" />
            <span class="hint">Stop rules fire here</span>
          </div>
        </div>

        <div class="field">
          <label for="b-source">Balance comes from</label>
          <select id="b-source" formControlName="balance_source">
            @for (s of sources; track s.value) {
              <option [value]="s.value">{{ s.label }}</option>
            }
          </select>
        </div>

        <div class="field" [class.invalid]="showError('growth_rate_pct')">
          <label for="b-growth">Annual growth % <span class="muted">(optional, used by the simulator)</span></label>
          <input id="b-growth" type="number" inputmode="decimal" step="0.1" min="-100" max="100" formControlName="growth_rate_pct" placeholder="7" />
        </div>

        <div class="form-actions">
          @if (bucket(); as b) {
            <button type="button" class="btn btn-danger" (click)="remove(b)" [disabled]="busy() || inUse()">
              {{ inUse() ? 'In use by flows' : 'Delete' }}
            </button>
          }
          <button type="submit" class="btn btn-primary" [disabled]="busy()">
            {{ busy() ? 'Saving…' : bucket() ? 'Save' : 'Add bucket' }}
          </button>
        </div>
      </form>
    </app-sheet>
  `,
})
export class BucketFormSheet {
  private readonly fb = inject(FormBuilder);
  private readonly store = inject(PlanStore);

  readonly open = input.required<boolean>();
  readonly bucket = input<Bucket | null>(null);
  readonly closed = output<void>();
  readonly saved = output<Bucket>();

  protected readonly kinds = BUCKET_KINDS;
  protected readonly sources = BALANCE_SOURCES;
  protected readonly busy = signal(false);
  protected readonly error = signal<string | null>(null);

  protected readonly inUse = computed(() => {
    const b = this.bucket();
    return b ? (this.store.flowCountByBucket().get(b.id) ?? 0) > 0 : false;
  });

  protected readonly form = this.fb.nonNullable.group({
    name: ['', [Validators.required, Validators.maxLength(80)]],
    kind: ['checking' as BucketKind, Validators.required],
    floor: [null as number | null, Validators.min(0)],
    target: [null as number | null, Validators.min(0)],
    balance_source: ['manual' as BalanceSource, Validators.required],
    growth_rate_pct: [null as number | null, [Validators.min(-100), Validators.max(100)]],
  });

  protected readonly kindHint = computed(() => {
    const hints: Partial<Record<BucketKind, string>> = {
      checking: 'Paychecks land here. Give it a floor.',
      hub: 'Where swept money waits before it is deployed.',
      policy_loan: 'Tracked as a negative balance.',
      runway: 'Give it a target so the stop rule can roll it into the engine.',
      engine: 'Balance arrives from the Rotation Dashboard in phase 5.',
    };
    return hints[this.form.controls.kind.value] ?? '';
  });

  constructor() {
    effect(() => {
      if (!this.open()) return;
      const b = this.bucket();
      this.error.set(null);
      this.form.reset(
        b
          ? {
              name: b.name,
              kind: b.kind,
              floor: fromApiMoney(b.floor),
              target: fromApiMoney(b.target),
              balance_source: b.balance_source,
              growth_rate_pct: b.growth_rate_pct === null ? null : Number(b.growth_rate_pct),
            }
          : { name: '', kind: 'checking', floor: null, target: null, balance_source: 'manual', growth_rate_pct: null },
      );
    });
    // Kind changes re-evaluate the hint.
    this.form.controls.kind.valueChanges.subscribe(() => this.kindTick.update((n) => n + 1));
  }
  private readonly kindTick = signal(0);

  protected showError(name: keyof typeof this.form.controls): boolean {
    const c = this.form.controls[name];
    return c.invalid && (c.touched || c.dirty);
  }

  protected async submit(): Promise<void> {
    this.form.markAllAsTouched();
    if (this.form.invalid) return;
    const v = this.form.getRawValue();
    const input: BucketInput = {
      name: v.name.trim(),
      kind: v.kind,
      floor: toApiMoney(v.floor),
      target: toApiMoney(v.target),
      balance_source: v.balance_source,
      growth_rate_pct: v.growth_rate_pct === null ? null : String(v.growth_rate_pct),
    };
    this.busy.set(true);
    this.error.set(null);
    try {
      const saved = await this.store.saveBucket(this.bucket()?.id ?? null, input);
      this.saved.emit(saved);
      this.closed.emit();
    } catch (err) {
      this.error.set(describeApiError(err));
    } finally {
      this.busy.set(false);
    }
  }

  protected async remove(b: Bucket): Promise<void> {
    if (!confirm(`Delete bucket “${b.name}”?`)) return;
    this.busy.set(true);
    try {
      await this.store.deleteBucket(b.id);
      this.closed.emit();
    } catch (err) {
      this.error.set(describeApiError(err));
    } finally {
      this.busy.set(false);
    }
  }
}
