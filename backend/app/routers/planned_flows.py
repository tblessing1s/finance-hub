from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.deps import DB
from app.models import Bucket, PlannedFlow
from app.schemas.money import from_cents, to_cents
from app.schemas.planned_flow import (
    PlannedFlowCreate,
    PlannedFlowOut,
    PlannedFlowUpdate,
    check_flow_invariants,
)

router = APIRouter(prefix="/planned-flows", tags=["planned-flows"])

BUCKET_REFS = ("from_bucket_id", "to_bucket_id", "redirect_to_bucket_id")

_WITH_BUCKETS = (
    selectinload(PlannedFlow.from_bucket),
    selectinload(PlannedFlow.to_bucket),
    selectinload(PlannedFlow.redirect_to_bucket),
)


def _get_or_404(db: Session, flow_id: int) -> PlannedFlow:
    flow = db.scalar(select(PlannedFlow).where(PlannedFlow.id == flow_id).options(*_WITH_BUCKETS))
    if flow is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"planned flow {flow_id} not found")
    return flow


def _assert_buckets_exist(db: Session, data: dict) -> None:
    ids = {data[k] for k in BUCKET_REFS if data.get(k) is not None}
    if not ids:
        return
    found = set(db.scalars(select(Bucket.id).where(Bucket.id.in_(ids))))
    missing = sorted(ids - found)
    if missing:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, f"bucket(s) not found: {missing}"
        )


def _apply(flow: PlannedFlow, data: dict) -> None:
    for field, value in data.items():
        if field == "amount":
            flow.amount_cents = to_cents(value)
        else:
            setattr(flow, field, value)


def _current_values(flow: PlannedFlow) -> dict:
    return {
        "name": flow.name,
        "from_bucket_id": flow.from_bucket_id,
        "to_bucket_id": flow.to_bucket_id,
        "amount": from_cents(flow.amount_cents),
        "amount_rule": flow.amount_rule,
        "cadence": flow.cadence,
        "anchor_date": flow.anchor_date,
        "stop_rule": flow.stop_rule,
        "stop_date": flow.stop_date,
        "redirect_to_bucket_id": flow.redirect_to_bucket_id,
        "match_pattern": flow.match_pattern,
        "active": flow.active,
    }


@router.get("", response_model=list[PlannedFlowOut])
def list_planned_flows(db: DB, active: bool | None = None) -> list[PlannedFlow]:
    stmt = select(PlannedFlow).options(*_WITH_BUCKETS)
    if active is not None:
        stmt = stmt.where(PlannedFlow.active == active)
    stmt = stmt.order_by(PlannedFlow.cadence, PlannedFlow.anchor_date, PlannedFlow.name)
    return list(db.scalars(stmt))


@router.post("", response_model=PlannedFlowOut, status_code=status.HTTP_201_CREATED)
def create_planned_flow(payload: PlannedFlowCreate, db: DB) -> PlannedFlow:
    data = payload.model_dump()
    _assert_buckets_exist(db, data)
    flow = PlannedFlow()
    _apply(flow, data)
    db.add(flow)
    db.commit()
    return _get_or_404(db, flow.id)


@router.get("/{flow_id}", response_model=PlannedFlowOut)
def get_planned_flow(flow_id: int, db: DB) -> PlannedFlow:
    return _get_or_404(db, flow_id)


@router.patch("/{flow_id}", response_model=PlannedFlowOut)
def update_planned_flow(flow_id: int, payload: PlannedFlowUpdate, db: DB) -> PlannedFlow:
    flow = _get_or_404(db, flow_id)
    changes = payload.model_dump(exclude_unset=True)
    for required in ("name", "cadence", "anchor_date", "active"):
        if required in changes and changes[required] is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"{required} cannot be null")
    merged = {**_current_values(flow), **changes}
    try:
        check_flow_invariants(merged)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc
    _assert_buckets_exist(db, changes)
    _apply(flow, changes)
    db.commit()
    db.expire(flow)
    return _get_or_404(db, flow_id)


@router.delete("/{flow_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_planned_flow(flow_id: int, db: DB) -> Response:
    flow = _get_or_404(db, flow_id)
    db.delete(flow)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
