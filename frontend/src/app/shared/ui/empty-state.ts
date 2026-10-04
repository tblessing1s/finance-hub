import { Component, input } from '@angular/core';

/** Says what to add first. Every screen ships empty, so this is the first thing the owner sees. */
@Component({
  selector: 'app-empty-state',
  template: `
    <div class="empty card">
      @if (step()) {
        <span class="tag">{{ step() }}</span>
      }
      <h3>{{ heading() }}</h3>
      <p>{{ body() }}</p>
      <ng-content />
    </div>
  `,
  styles: `
    .empty {
      padding: 22px 18px; text-align: center;
      display: flex; flex-direction: column; align-items: center; gap: 8px;
      h3 { font-size: 16px; }
      p { margin: 0; color: var(--muted); max-width: 36ch; }
    }
    .tag { margin-bottom: 4px; }
  `,
})
export class EmptyState {
  readonly heading = input.required<string>();
  readonly body = input('');
  readonly step = input('');
}
