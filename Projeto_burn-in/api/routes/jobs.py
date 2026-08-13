"""
routes/jobs.py
Criação, controle e finalização de jobs de burn-in.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from database import get_db, Job, Equipamento
from models.schemas import JobCreate, JobOut, JobFinalizar

router = APIRouter()


@router.post("", response_model=JobOut, status_code=201)
def criar_job(payload: JobCreate, db: Session = Depends(get_db)):
    """Operador cria um job de burn-in para um equipamento."""
    if payload.duracao_horas not in (4, 8, 12, 24):
        raise HTTPException(status_code=400, detail="Duração deve ser 4, 8, 12 ou 24 horas.")

    eq = db.query(Equipamento).filter(Equipamento.id == payload.equipamento_id).first()
    if not eq:
        raise HTTPException(status_code=404, detail="Equipamento não encontrado.")

    job = Job(
        equipamento_id=payload.equipamento_id,
        duracao_horas=payload.duracao_horas,
        status="PENDENTE",
        criado_em=datetime.now(timezone.utc),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("", response_model=list[JobOut])
def listar_jobs(db: Session = Depends(get_db)):
    return db.query(Job).order_by(Job.id.desc()).all()


@router.get("/{job_id}", response_model=JobOut)
def buscar_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado.")
    return job


@router.post("/{job_id}/iniciar", response_model=JobOut)
def iniciar_job(job_id: int, db: Session = Depends(get_db)):
    """Agent chama quando começa a executar os testes."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado.")
    if job.status != "PENDENTE":
        raise HTTPException(status_code=400, detail=f"Job já está com status '{job.status}'.")

    job.status = "EM_EXECUCAO"
    job.iniciado_em = datetime.now(timezone.utc)
    db.commit()
    db.refresh(job)
    return job


@router.post("/{job_id}/finalizar", response_model=JobOut)
def finalizar_job(job_id: int, payload: JobFinalizar, db: Session = Depends(get_db)):
    """Agent chama ao terminar os testes."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado.")

    job.status = "APROVADO" if payload.aprovado else "REPROVADO"
    job.aprovado = payload.aprovado
    job.motivo_reprovacao = payload.motivo_reprovacao
    job.duracao_real_segundos = payload.duracao_real_segundos
    job.finalizado_em = datetime.now(timezone.utc)
    db.commit()
    db.refresh(job)
    return job