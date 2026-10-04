import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { PlannedFlow, PlannedFlowInput } from './models';

@Injectable({ providedIn: 'root' })
export class PlannedFlowsService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/planned-flows';

  list(): Promise<PlannedFlow[]> {
    return firstValueFrom(this.http.get<PlannedFlow[]>(this.base));
  }

  create(input: PlannedFlowInput): Promise<PlannedFlow> {
    return firstValueFrom(this.http.post<PlannedFlow>(this.base, input));
  }

  update(id: number, patch: Partial<PlannedFlowInput>): Promise<PlannedFlow> {
    return firstValueFrom(this.http.patch<PlannedFlow>(`${this.base}/${id}`, patch));
  }

  remove(id: number): Promise<void> {
    return firstValueFrom(this.http.delete<void>(`${this.base}/${id}`));
  }
}
