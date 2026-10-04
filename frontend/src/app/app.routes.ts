import { Routes } from '@angular/router';

// Four tabs, one data model. Only Plan is functional in phase 1, so the app opens there;
// phase 2 moves the default to Now once balance snapshots exist.
export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'plan' },
  {
    path: 'now',
    title: 'Now · Finance Hub',
    loadComponent: () => import('./features/now/now-page').then((m) => m.NowPage),
  },
  {
    path: 'plan',
    title: 'Plan · Finance Hub',
    loadComponent: () => import('./features/plan/plan-page').then((m) => m.PlanPage),
  },
  {
    path: 'simulate',
    title: 'Simulate · Finance Hub',
    loadComponent: () =>
      import('./features/simulate/simulate-page').then((m) => m.SimulatePage),
  },
  {
    path: 'expenses',
    title: 'Expenses · Finance Hub',
    loadComponent: () =>
      import('./features/expenses/expenses-page').then((m) => m.ExpensesPage),
  },
  { path: '**', redirectTo: 'plan' },
];
