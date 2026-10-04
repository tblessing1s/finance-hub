import { HttpErrorResponse } from '@angular/common/http';

/** Reduce a FastAPI error body to one readable line for a form sheet. */
export function describeApiError(err: unknown): string {
  if (err instanceof HttpErrorResponse) {
    const detail = err.error?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((d: { loc?: (string | number)[]; msg?: string }) => {
          const field = (d.loc ?? []).filter((p) => p !== 'body').join('.');
          const msg = (d.msg ?? '').replace(/^Value error, /, '');
          return field ? `${field}: ${msg}` : msg;
        })
        .join('; ');
    }
    if (err.status === 0) return 'Cannot reach the API. Is the backend running on :8000?';
    return `${err.status} ${err.statusText}`;
  }
  return err instanceof Error ? err.message : 'Something went wrong';
}
