import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

import { EmptyState } from '../../shared/ui/empty-state';

@Component({
  selector: 'app-now-page',
  imports: [EmptyState, RouterLink],
  template: `
    <section class="page">
      <header class="page-head"><h1>Now</h1></header>
      <app-empty-state
        heading="Nothing to show yet"
        body="Now fills in once every bucket has a balance snapshot. Enter the plan first, then come back to record balances. Snapshots arrive in phase 2."
      >
        <a class="btn" routerLink="/plan">Go to Plan</a>
      </app-empty-state>
    </section>
  `,
})
export class NowPage {}
