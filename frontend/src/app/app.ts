import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

interface Tab {
  path: string;
  label: string;
  icon: string; // inline SVG path data, 24x24 viewBox
}

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  protected readonly tabs: Tab[] = [
    { path: '/now', label: 'Now', icon: 'M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm1 5h-2v6l5 3 1-1.7-4-2.3V7z' },
    { path: '/plan', label: 'Plan', icon: 'M4 5h16v2H4zm0 6h16v2H4zm0 6h10v2H4z' },
    { path: '/simulate', label: 'Simulate', icon: 'M3 17l6-6 4 4 8-8v4h2V3h-8v2h4l-6 6-4-4-7 7z' },
    { path: '/expenses', label: 'Expenses', icon: 'M4 4h16v4H4zm0 6h16v10H4zm2 2v6h12v-6z' },
  ];
}
