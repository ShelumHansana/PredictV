"""Run a check, and read back the checks this browser has made."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import HISTORY_LIMIT
from app.db import Diagnosis, Feedback, get_db
from app.deps import client_id
from app.engine import diagnose
from app.schemas import DiagnoseRequest, DiagnosisOut, DiagnosisSummary, FeedbackIn
from app.services import mixture_model, symptom_model

router = APIRouter(prefix="/api/diagnoses", tags=["diagnoses"])


def _own(db: Session, diagnosis_id: str, cid: str) -> Diagnosis:
    row = db.get(Diagnosis, diagnosis_id)
    # same answer for "not there" and "not yours", so ids cannot be probed
    if row is None or row.client_id != cid:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Check not found")
    return row


@router.post("", response_model=DiagnosisOut, status_code=status.HTTP_201_CREATED)
def create(req: DiagnoseRequest, cid: str = Depends(client_id), db: Session = Depends(get_db)) -> Diagnosis:
    e = req.emission
    if (e.co_percent is None) != (e.hc_ppm is None):
        raise HTTPException(422, "Enter both CO and HC, or leave both empty.")
    result = diagnose(
        symptoms=req.symptoms,
        service_km=req.service.model_dump(),
        mileage_km=req.bike.mileage_km,
        readings={"CO": e.co_percent, "HC": e.hc_ppm, "CO2": e.co2_percent, "O2": e.o2_percent, "Lambda": e.lambda_value},
        model=mixture_model,
        symptom_model=symptom_model,
    )
    row = Diagnosis(
        id=str(uuid.uuid4()), client_id=cid, bike_name=req.bike.name, overall=result["overall"],
        answers=req.model_dump(), result=result,
    )
    db.add(row)
    db.flush()
    # keep only the newest HISTORY_LIMIT checks for this browser
    old = db.scalars(
        select(Diagnosis.id).where(Diagnosis.client_id == cid)
        .order_by(Diagnosis.created_at.desc()).offset(HISTORY_LIMIT)
    ).all()
    if old:
        db.execute(delete(Feedback).where(Feedback.diagnosis_id.in_(old)))
        db.execute(delete(Diagnosis).where(Diagnosis.id.in_(old)))
    db.commit()
    return row


@router.get("", response_model=list[DiagnosisSummary])
def history(cid: str = Depends(client_id), db: Session = Depends(get_db)) -> list[DiagnosisSummary]:
    rows = db.scalars(
        select(Diagnosis).where(Diagnosis.client_id == cid).order_by(Diagnosis.created_at.desc()).limit(HISTORY_LIMIT)
    ).all()
    return [
        DiagnosisSummary(
            id=r.id, created_at=r.created_at, bike_name=r.bike_name, overall=r.overall,
            top_fault=r.result["faults"][0]["id"] if r.result["faults"] else None,
            fault_count=len(r.result["faults"]), has_feedback=r.feedback is not None,
        )
        for r in rows
    ]


@router.get("/{diagnosis_id}", response_model=DiagnosisOut)
def read(diagnosis_id: str, cid: str = Depends(client_id), db: Session = Depends(get_db)) -> Diagnosis:
    return _own(db, diagnosis_id, cid)


@router.delete("/{diagnosis_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove(diagnosis_id: str, cid: str = Depends(client_id), db: Session = Depends(get_db)) -> Response:
    db.delete(_own(db, diagnosis_id, cid))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{diagnosis_id}/feedback", response_model=DiagnosisOut)
def give_feedback(
    diagnosis_id: str, body: FeedbackIn, cid: str = Depends(client_id), db: Session = Depends(get_db)
) -> Diagnosis:
    row = _own(db, diagnosis_id, cid)
    note = (body.note or "").strip() or None
    if row.feedback:
        row.feedback.confirmed_fault, row.feedback.note = body.confirmed_fault, note
    else:
        row.feedback = Feedback(confirmed_fault=body.confirmed_fault, note=note)
    db.commit()
    db.refresh(row)
    return row
