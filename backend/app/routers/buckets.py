from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import exists, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.deps import DB
from app.models import Bucket, LedgerEntry, PlannedFlow
from app.schemas.bucket import BucketCreate, BucketOut, BucketUpdate
from app.schemas.money import to_cents

router = APIRouter(prefix="/buckets", tags=["buckets"])

MONEY_FIELDS = {"floor": "floor_cents", "target": "target_cents"}


def _get_or_404(db: Session, bucket_id: int) -> Bucket:
    bucket = db.get(Bucket, bucket_id)
    if bucket is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"bucket {bucket_id} not found")
    return bucket


def _apply(bucket: Bucket, data: dict) -> None:
    for field, value in data.items():
        if field in MONEY_FIELDS:
            setattr(bucket, MONEY_FIELDS[field], to_cents(value))
        else:
            setattr(bucket, field, value)


def _commit_or_409(db: Session, name: str) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"a bucket named {name!r} already exists"
        ) from exc


@router.get("", response_model=list[BucketOut])
def list_buckets(db: DB) -> list[Bucket]:
    return list(db.scalars(select(Bucket).order_by(Bucket.name)))


@router.post("", response_model=BucketOut, status_code=status.HTTP_201_CREATED)
def create_bucket(payload: BucketCreate, db: DB) -> Bucket:
    bucket = Bucket()
    _apply(bucket, payload.model_dump())
    db.add(bucket)
    _commit_or_409(db, payload.name)
    db.refresh(bucket)
    return bucket


@router.get("/{bucket_id}", response_model=BucketOut)
def get_bucket(bucket_id: int, db: DB) -> Bucket:
    return _get_or_404(db, bucket_id)


@router.patch("/{bucket_id}", response_model=BucketOut)
def update_bucket(bucket_id: int, payload: BucketUpdate, db: DB) -> Bucket:
    bucket = _get_or_404(db, bucket_id)
    changes = payload.model_dump(exclude_unset=True)
    if changes.get("name") is None and "name" in changes:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "name cannot be null")
    if changes.get("kind") is None and "kind" in changes:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "kind cannot be null")
    if changes.get("balance_source") is None and "balance_source" in changes:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "balance_source cannot be null")
    _apply(bucket, changes)
    _commit_or_409(db, bucket.name)
    db.refresh(bucket)
    return bucket


@router.delete("/{bucket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bucket(bucket_id: int, db: DB) -> Response:
    bucket = _get_or_404(db, bucket_id)
    in_flows = db.scalar(
        select(
            exists().where(
                or_(PlannedFlow.from_bucket_id == bucket_id, PlannedFlow.to_bucket_id == bucket_id)
            )
        )
    )
    if in_flows:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"bucket {bucket.name!r} is used by a planned flow; edit or delete those flows first",
        )
    in_ledger = db.scalar(
        select(
            exists().where(
                or_(LedgerEntry.from_bucket_id == bucket_id, LedgerEntry.to_bucket_id == bucket_id)
            )
        )
    )
    if in_ledger:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"bucket {bucket.name!r} has ledger entries and cannot be deleted",
        )
    db.delete(bucket)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
