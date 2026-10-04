import {
  Component,
  ElementRef,
  afterRenderEffect,
  input,
  output,
  viewChild,
} from '@angular/core';

/**
 * Bottom sheet on phones, centered dialog above 720px. Built on <dialog> so focus, ESC and
 * the backdrop come from the platform.
 */
@Component({
  selector: 'app-sheet',
  template: `
    <dialog #dlg class="sheet" (close)="closed.emit()" (click)="onBackdrop($event)" (cancel)="onCancel($event)">
      <div class="sheet-body" (click)="$event.stopPropagation()">
        <header class="sheet-head">
          <h1>{{ title() }}</h1>
          <button type="button" class="btn btn-ghost btn-sm" (click)="close()" aria-label="Close">
            Close
          </button>
        </header>
        <div class="sheet-content">
          <ng-content />
        </div>
      </div>
    </dialog>
  `,
  styles: `
    .sheet {
      padding: 0; border: 0; background: transparent;
      width: 100%; max-width: none; max-height: 100dvh; margin: auto 0 0;
      &::backdrop { background: rgb(0 0 0 / 0.45); }
    }
    .sheet-body {
      background: var(--surface); color: var(--text);
      border-radius: 18px 18px 0 0; border: 1px solid var(--hairline);
      max-height: 92dvh; display: flex; flex-direction: column;
      padding-bottom: env(safe-area-inset-bottom);
    }
    .sheet-head {
      display: flex; align-items: center; justify-content: space-between;
      padding: 14px 16px 10px; border-bottom: 1px solid var(--hairline);
      h1 { font-size: 17px; }
    }
    .sheet-content { padding: 16px; overflow-y: auto; }
    @media (min-width: 720px) {
      .sheet { margin: auto; width: 480px; }
      .sheet-body { border-radius: 16px; max-height: 86dvh; }
    }
  `,
})
export class Sheet {
  readonly open = input.required<boolean>();
  readonly title = input('');
  readonly closed = output<void>();

  private readonly dlg = viewChild.required<ElementRef<HTMLDialogElement>>('dlg');

  constructor() {
    afterRenderEffect(() => {
      const el = this.dlg().nativeElement;
      if (this.open() && !el.open) el.showModal();
      else if (!this.open() && el.open) el.close();
    });
  }

  close(): void {
    this.dlg().nativeElement.close();
  }

  protected onBackdrop(event: MouseEvent): void {
    if (event.target === this.dlg().nativeElement) this.close();
  }

  protected onCancel(event: Event): void {
    event.preventDefault(); // ESC: route through close() so one `closed` fires
    this.close();
  }
}
