import { Component, computed, input, output } from '@angular/core';

import { Bucket, PlannedFlow } from '../../core/api/models';
import { MapNode, formatNet, layoutFlowMap } from './flow-map.layout';

/**
 * Inline-SVG map of the plan: buckets in rows from Income to Outside, flows as arrows whose
 * thickness tracks monthly volume. Tapping a bucket or a single-flow arrow opens its editor.
 */
@Component({
  selector: 'app-flow-map',
  template: `
    @if (layout().nodes.length) {
      <div class="map card">
        <svg
          [attr.viewBox]="'0 0 ' + layout().width + ' ' + layout().height"
          [style.aspect-ratio]="layout().width + ' / ' + layout().height"
          role="img"
          aria-label="Map of planned flows between buckets"
        >
          <defs>
            <marker id="fm-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto-start-reverse">
              <path d="M0,0 L10,5 L0,10 z" fill="var(--muted)" />
            </marker>
            <marker id="fm-arrow-accent" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto-start-reverse">
              <path d="M0,0 L10,5 L0,10 z" fill="var(--accent)" />
            </marker>
          </defs>

          @for (e of layout().edges; track e.id) {
            <g
              class="edge"
              [class.rule]="e.kind === 'rule'"
              [class.redirect]="e.kind === 'redirect'"
              [class.inactive]="!e.active"
              [class.tappable]="!!e.flow"
              (click)="e.flow && flowTap.emit(e.flow)"
            >
              <path class="hit" [attr.d]="e.path" />
              <path
                class="line"
                [attr.d]="e.path"
                [attr.stroke-width]="e.width"
                [attr.marker-end]="e.kind === 'fixed' ? 'url(#fm-arrow-accent)' : 'url(#fm-arrow)'"
              />
              <text class="edge-label" [attr.x]="e.labelX" [attr.y]="e.labelY" text-anchor="middle" dominant-baseline="middle">
                {{ e.label }}
              </text>
            </g>
          }

          @for (n of layout().nodes; track n.id) {
            <g
              class="node"
              [class.external]="n.external"
              [class.tappable]="!n.external"
              [attr.transform]="'translate(' + n.x + ',' + n.y + ')'"
              (click)="n.bucketId !== null && bucketTap.emit(n.bucketId)"
            >
              <rect [attr.width]="n.w" [attr.height]="n.h" rx="10" />
              <text class="name" [attr.x]="n.w / 2" [attr.y]="n.external ? n.h / 2 : 17" text-anchor="middle" dominant-baseline="middle">
                {{ fit(n.label, n.w) }}
              </text>
              @if (!n.external) {
                <text
                  class="net"
                  [class.pos]="(n.netMonthly ?? 0) > 0"
                  [class.neg]="(n.netMonthly ?? 0) < 0"
                  [attr.x]="n.w / 2"
                  y="33"
                  text-anchor="middle"
                  dominant-baseline="middle"
                >
                  {{ net(n) }}
                </text>
              }
            </g>
          }
        </svg>
        <p class="legend small">
          <span><i class="sw solid"></i> fixed amount</span>
          <span><i class="sw dashed"></i> rule</span>
          <span><i class="sw dotted"></i> after stop rule</span>
          <span>thickness = $/month</span>
          @if (hasRule()) {
            <span>* net excludes rule-based flows</span>
          }
        </p>
      </div>
    }
  `,
  styles: `
    .map { padding: 10px 8px 6px; }
    svg { display: block; width: 100%; height: auto; max-width: 560px; margin: 0 auto; overflow: visible; }
    .node rect { fill: var(--surface); stroke: var(--hairline); stroke-width: 1.2; }
    .node.external rect { fill: var(--bg); stroke-dasharray: 3 3; }
    .node text { fill: var(--text); font-size: 12px; font-weight: 600; }
    .node.external text { fill: var(--muted); font-weight: 500; }
    .node .net { font-size: 10.5px; font-weight: 500; fill: var(--muted); font-variant-numeric: tabular-nums; }
    .node .net.pos { fill: var(--green); }
    .node .net.neg { fill: var(--red); }
    .edge .hit { fill: none; stroke: transparent; stroke-width: 16; }
    .edge .line { fill: none; stroke: var(--accent); stroke-linecap: round; opacity: 0.85; }
    .edge.rule .line { stroke: var(--muted); stroke-dasharray: 6 4; }
    .edge.redirect .line { stroke: var(--muted); stroke-dasharray: 2 4; }
    .edge.inactive { opacity: 0.35; }
    .edge-label {
      font-size: 10.5px; fill: var(--text); font-variant-numeric: tabular-nums;
      paint-order: stroke; stroke: var(--surface); stroke-width: 4px; stroke-linejoin: round;
    }
    .tappable { cursor: pointer; }
    .tappable:hover rect { stroke: var(--accent); }
    .tappable:hover .line { opacity: 1; }
    .legend {
      display: flex; flex-wrap: wrap; gap: 6px 14px; justify-content: center;
      margin: 8px 0 0; padding-top: 8px; border-top: 1px solid var(--hairline);
      span { display: inline-flex; align-items: center; gap: 5px; }
    }
    .sw { display: inline-block; width: 18px; border-top: 2px solid var(--accent); }
    .sw.dashed { border-top-style: dashed; border-color: var(--muted); }
    .sw.dotted { border-top-style: dotted; border-color: var(--muted); }
  `,
})
export class FlowMap {
  readonly buckets = input.required<Bucket[]>();
  readonly flows = input.required<PlannedFlow[]>();
  readonly bucketTap = output<number>();
  readonly flowTap = output<PlannedFlow>();

  protected readonly layout = computed(() => layoutFlowMap(this.buckets(), this.flows()));
  protected readonly hasRule = computed(() => this.layout().nodes.some((n) => n.hasRuleFlow));

  protected net(n: MapNode): string {
    return formatNet(n.netMonthly, n.hasRuleFlow);
  }

  /** SVG text has no ellipsis; trim to the node width at ~6.6px per character. */
  protected fit(label: string, width: number): string {
    const max = Math.max(4, Math.floor((width - 12) / 6.6));
    return label.length <= max ? label : label.slice(0, max - 1).trimEnd() + '…';
  }
}
