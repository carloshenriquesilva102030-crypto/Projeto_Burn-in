"""
routes/metricas.py
Recebe e consulta métricas e eventos de um job.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db, Job, Metrica, Evento
from models.schemas import MetricaIn, MetricaOut, EventoIn, EventoOut

router = APIRouter()


# ---------------------------------------------------------------------------
# Métricas
# ---------------------------------------------------------------------------

@router.post("/{job_id}/metricas", response_model=MetricaOut, status_code=201)
def receber_metrica(job_id: int, payload: MetricaIn, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado.")

    metrica = Metrica(job_id=job_id, **payload.model_dump())
    db.add(metrica)
    db.commit()
    db.refresh(metrica)
    return metrica


@router.get("/{job_id}/metricas", response_model=list[MetricaOut])
def listar_metricas(job_id: int, db: Session = Depends(get_db)):
    return db.query(Metrica).filter(Metrica.job_id == job_id).order_by(Metrica.timestamp).all()


# ---------------------------------------------------------------------------
# Eventos
# ---------------------------------------------------------------------------

@router.post("/{job_id}/eventos", response_model=EventoOut, status_code=201)
def receber_evento(job_id: int, payload: EventoIn, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado.")

    evento = Evento(job_id=job_id, **payload.model_dump())
    db.add(evento)
    db.commit()
    db.refresh(evento)
    return evento


@router.get("/{job_id}/eventos", response_model=list[EventoOut])
def listar_eventos(job_id: int, db: Session = Depends(get_db)):
    return db.query(Evento).filter(Evento.job_id == job_id).order_by(Evento.timestamp).all()