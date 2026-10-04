import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

import { EmptyState } from '../../shared/ui/empty-state';

@Component({
  selector: 'app-simulate-page',
  imports: [EmptyState, RouterLink],
  template: `
    <section class="page">
      <header class="page-head"><h1>Simulate</h1></header>
      <app-empty-state
        heading="Nothing to simulate yet"
        body="The simulator needs at least one planned flow and one balance snapshot. The engine and chart arrive in phase 3."
      >
        <a class="btn" routerLink="/plan">Go to Plan</a>
      </app-empty-state>
    </section>
  `,
})
export class SimulatePage {}
