import { Component, computed, effect, inject, input, output, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { toSignal } from '@angular/core/rxjs-interop';

import { describeApiError } from '../../core/api/api-error';
import {
  AMOUNT_RULES,
  AmountRule,
  CADENCES,
  Cadence,
  PlannedFlow,
  PlannedFlowInput,
  STOP_RULES,
  StopRule,
} from '../../core/api/models';
import { fromApiMoney, toApiMoney } from '../../core/money';
import { PlanStore } from '../../core/plan.store';
import { Sheet } from '../../shared/ui/sheet';

type AmountMode = 'fixed' | 'rule';

/** Add or edit a planned flow. Pass `flow` to edit; null adds (optionally with a preset cadence). */
@Component({
  selector: 'app-flow-form-sheet',
  imports: [ReactiveFormsModule, Sheet],
  template: `
    <app-sheet [open]="open()" [title]="flow() ? 'Edit flow' : 'New flow'" (closed)="closed.emit()">
      <form [formGroup]="form" (ngSubmit)="submit()" novalidate>
        @if (error()) {
          <p class="form-error" role="alert">{{ error() }}</p>
        }

        <div class="field" [class.invalid]="showError('name')">
          <label for="f-name">Name</label>
          <input id="f-name" formControlName="name" placeholder="Paycheck" autocomplete="off" />
        </div>

        <div class="field-row">
          <div class="field">
            <label for="f-from">From</label>
            <select id="f-from" formControlName="from_bucket_id">
              <option [ngValue]="null">Outside (income)</option>
              @for (b of buckets(); track b.id) {
                <option [ngValue]="b.id">{{ b.name }}</option>
              }
            </select>
          </div>
          <div class="field">
            <label for="f-to">To</label>
            <select id="f-to" formControlName="to_bucket_id">
              <option [ngValue]="null">Outside (a bill)</option>
              @for (b of buckets(); track b.id) {
                <option [ngValue]="b.id">{{ b.name }}</option>
              }
            </select>
          </div>
        </div>
        @if (endpointError(); as msg) {
          <p class="form-error">{{ msg }}</p>
        }

        <div class="field">
          <label>Amount</label>
          <div class="segmented" role="radiogroup" aria-label="Amount mode">
            <button type="button" role="radio" [attr.aria-checked]="mode() === 'fixed'" [class.on]="mode() === 'fixed'" (click)="mode.set('fixed')">Fixed</button>
            <button type="button" role="radio" [attr.aria-checked]="mode() === 'rule'" [class.on]="mode() === 'rule'" (click)="mode.set('rule')">Rule</button>
          </div>
        </div>

        @if (mode() === 'fixed') {
          <div class="field" [class.invalid]="showError('amount')">
            <label for="f-amount">Amount ($)</label>
            <input id="f-amount" type="number" inputmode="decimal" min="0.01" step="0.01" formControlName="amount" placeholder="3200" />
          </div>
        } @else {
          <div class="field">
            <label for="f-rule">Rule</label>
            <select id="f-rule" formControlName="amount_rule">
              @for (r of rules; track r.value) {
                <option [value]="r.value">{{ r.label }}</option>
              }
            </select>
            <span class="hint">Rules read the From bucket's balance and floor.</span>
          </div>
        }

        <div class="field-row">
          <div class="field">
            <label for="f-cadence">Cadence</label>
            <select id="f-cadence" formControlName="cadence">
              @for (c of cadences; track c.value) {
                <option [value]="c.value">{{ c.label }}</option>
              }
            </select>
          </div>
          <div class="field" [class.invalid]="showError('anchor_date')">
            <label for="f-anchor">{{ anchorLabel() }}</label>
            <input id="f-anchor" type="date" formControlName="anchor_date" />
          </div>
        </div>

        <div class="field">
          <label for="f-stop">Stops</label>
          <select id="f-stop" formControlName="stop_rule">
            <option [ngValue]="null">Never</option>
            @for (s of stopRules; track s.value) {
              <option [ngValue]="s.value">{{ s.label }}</option>
            }
          </select>
        </div>

        @if (stopRule() === 'date') {
          <div class="field" [class.invalid]="showError('stop_date')">
            <label for="f-stopdate">Stop date</label>
            <input id="f-stopdate" type="date" formControlName="stop_date" />
          </div>
        }

        @if (stopRule()) {
          <div class="field">
            <label for="f-redirect">After it stops, send the amount to</label>
            <select id="f-redirect" formControlName="redirect_to_bucket_id">
              <option [ngValue]="null">Nowhere (flow just ends)</option>
              @for (b of buckets(); track b.id) {
                <option [ngValue]="b.id">{{ b.name }}</option>
              }
            </select>
            <span class="hint">This is how runway rolls into the engine.</span>
          </div>
        }

        <details class="advanced">
          <summary class="small">Advanced</summary>
          <div class="field">
            <label for="f-match">CSV match text <span class="muted">(optional)</span></label>
            <input id="f-match" formControlName="match_pattern" placeholder="AMERITAS" autocomplete="off" />
            <span class="hint">Imported transactions containing this text record the actual for this flow.</span>
          </div>
          <label class="check">
            <input type="checkbox" formControlName="active" />
            <span>Active (paused flows are kept but skipped by the simulator)</span>
          </label>
        </details>

        <div class="form-actions">
          @if (flow(); as f) {
            <button type="button" class="btn btn-danger" (click)="remove(f)" [disabled]="busy()">Delete</button>
          }
          <button type="submit" class="btn btn-primary" [disabled]="busy()">
            {{ busy() ? 'Saving…' : flow() ? 'Save' : 'Add flow' }}
          </button>
        </div>
      </form>
    </app-sheet>
  `,
  styles: `
    .advanced { margin: 4px 0 12px; summary { cursor: pointer; padding: 6px 0; } }
  `,
})
export class FlowFormSheet {
  private readonly fb = inject(FormBuilder);
  private readonly store = inject(PlanStore);

  readonly open = input.required<boolean>();
  readonly flow = input<PlannedFlow | null>(null);
  readonly presetCadence = input<Cadence | null>(null);
  readonly closed = output<void>();
  readonly saved = output<PlannedFlow>();

  protected readonly buckets = this.store.buckets;
  protected readonly cadences = CADENCES;
  protected readonly rules = AMOUNT_RULES;
  protected readonly stopRules = STOP_RULES;
  protected readonly mode = signal<AmountMode>('fixed');
  protected readonly busy = signal(false);
  protected readonly error = signal<string | null>(null);

  protected readonly form = this.fb.group({
    name: this.fb.nonNullable.control('', [Validators.required, Validators.maxLength(120)]),
    from_bucket_id: this.fb.control<number | null>(null),
    to_bucket_id: this.fb.control<number | null>(null),
    amount: this.fb.control<number | null>(null, Validators.min(0.01)),
    amount_rule: this.fb.nonNullable.control<AmountRule>('sweep_above_floor'),
    cadence: this.fb.nonNullable.control<Cadence>('per_paycheck', Validators.required),
    anchor_date: this.fb.nonNullable.control('', Validators.required),
    stop_rule: this.fb.control<StopRule | null>(null),
    stop_date: this.fb.control<string | null>(null),
    redirect_to_bucket_id: this.fb.control<number | null>(null),
    match_pattern: this.fb.control<string | null>(null),
    active: this.fb.nonNullable.control(true),
  });

  private readonly values = toSignal(this.form.valueChanges, { initialValue: this.form.value });

  protected readonly stopRule = computed(() => this.values().stop_rule ?? null);
  protected readonly anchorLabel = computed(
    () => CADENCES.find((c) => c.value === this.values().cadence)?.anchorLabel ?? 'Anchor date',
  );
  protected readonly endpointError = computed(() => {
    const v = this.values();
    if (v.from_bucket_id == null && v.to_bucket_id == null) return 'Pick a From or a To bucket.';
    if (v.from_bucket_id != null && v.from_bucket_id === v.to_bucket_id) return 'From and To must differ.';
    if (this.mode() === 'rule' && v.from_bucket_id == null) return 'A rule needs a From bucket to read.';
    return null;
  });

  constructor() {
    effect(() => {
      if (!this.open()) return;
      const f = this.flow();
      this.error.set(null);
      this.mode.set(f?.amount_rule ? 'rule' : 'fixed');
      this.form.reset({
        name: f?.name ?? '',
        from_bucket_id: f?.from_bucket_id ?? null,
        to_bucket_id: f?.to_bucket_id ?? null,
        amount: fromApiMoney(f?.amount),
        amount_rule: f?.amount_rule ?? 'sweep_above_floor',
        cadence: f?.cadence ?? this.presetCadence() ?? 'per_paycheck',
        anchor_date: f?.anchor_date ?? todayIso(),
        stop_rule: f?.stop_rule ?? null,
        stop_date: f?.stop_date ?? null,
        redirect_to_bucket_id: f?.redirect_to_bucket_id ?? null,
        match_pattern: f?.match_pattern ?? null,
        active: f?.active ?? true,
      });
    });
  }

  protected showError(name: keyof typeof this.form.controls): boolean {
    const c = this.form.controls[name];
    return c.invalid && (c.touched || c.dirty);
  }

  protected async submit(): Promise<void> {
    this.form.markAllAsTouched();
    const v = this.form.getRawValue();
    const fixed = this.mode() === 'fixed';
    if (fixed && (v.amount === null || v.amount <= 0)) {
      this.error.set('Enter an amount above zero, or switch to a rule.');
      return;
    }
    if (v.stop_rule === 'date' && !v.stop_date) {
      this.error.set('Pick the stop date.');
      return;
    }
    if (this.form.invalid || this.endpointError()) return;

    const input: PlannedFlowInput = {
      name: v.name.trim(),
      from_bucket_id: v.from_bucket_id,
      to_bucket_id: v.to_bucket_id,
      amount: fixed ? toApiMoney(v.amount) : null,
      amount_rule: fixed ? null : v.amount_rule,
      cadence: v.cadence,
      anchor_date: v.anchor_date,
      stop_rule: v.stop_rule,
      stop_date: v.stop_rule === 'date' ? v.stop_date : null,
      redirect_to_bucket_id: v.stop_rule ? v.redirect_to_bucket_id : null,
      match_pattern: v.match_pattern?.trim() || null,
      active: v.active,
    };
    this.busy.set(true);
    this.error.set(null);
    try {
      const saved = await this.store.saveFlow(this.flow()?.id ?? null, input);
      this.saved.emit(saved);
      this.closed.emit();
    } catch (err) {
      this.error.set(describeApiError(err));
    } finally {
      this.busy.set(false);
    }
  }

  protected async remove(f: PlannedFlow): Promise<void> {
    if (!confirm(`Delete flow “${f.name}”?`)) return;
    this.busy.set(true);
    try {
      await this.store.deleteFlow(f.id);
      this.closed.emit();
    } catch (err) {
      this.error.set(describeApiError(err));
    } finally {
      this.busy.set(false);
    }
  }
}

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}
