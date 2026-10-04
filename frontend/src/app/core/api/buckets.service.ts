import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { Bucket, BucketInput } from './models';

@Injectable({ providedIn: 'root' })
export class BucketsService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/buckets';

  list(): Promise<Bucket[]> {
    return firstValueFrom(this.http.get<Bucket[]>(this.base));
  }

  create(input: BucketInput): Promise<Bucket> {
    return firstValueFrom(this.http.post<Bucket>(this.base, input));
  }

  update(id: number, patch: Partial<BucketInput>): Promise<Bucket> {
    return firstValueFrom(this.http.patch<Bucket>(`${this.base}/${id}`, patch));
  }

  remove(id: number): Promise<void> {
    return firstValueFrom(this.http.delete<void>(`${this.base}/${id}`));
  }
}
