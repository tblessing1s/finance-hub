import { Component } from '@angular/core';

import { EmptyState } from '../../shared/ui/empty-state';

@Component({
  selector: 'app-expenses-page',
  imports: [EmptyState],
  template: `
    <section class="page">
      <header class="page-head"><h1>Expenses</h1></header>
      <app-empty-state
        heading="No transactions yet"
        body="Categories, lumpy items and the monthly CSV import for Wells Fargo and Capital One arrive in phase 4."
      />
    </section>
  `,
})
export class ExpensesPage {}
