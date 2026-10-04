import { provideRouter } from '@angular/router';
import { TestBed } from '@angular/core/testing';
import { App } from './app';

describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [provideRouter([])],
    }).compileComponents();
  });

  it('renders the four tabs', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const labels = Array.from(
      (fixture.nativeElement as HTMLElement).querySelectorAll('nav a span'),
    ).map((el) => el.textContent?.trim());
    expect(labels).toEqual(['Now', 'Plan', 'Simulate', 'Expenses']);
  });
});
