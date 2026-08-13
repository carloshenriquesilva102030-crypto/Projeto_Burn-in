"""
routes/equipamentos.py
Registro e consulta de equipamentos.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from database import get_db, Equipamento, Job
from models.schemas import EquipamentoIn, EquipamentoOut, JobOut

router = APIRouter()


@router.post("", response_model=EquipamentoOut, status_code=201)
def registrar_equipamento(payload: EquipamentoIn, db: Session = Depends(get_db)):
    """
    Agent chama este endpoint ao iniciar.
    Se o MAC já existe, atualiza os dados e o último contato.
    Se não existe, cria um novo equipamento.
    """
    equipamento = db.query(Equipamento).filter(
        Equipamento.mac_address == payload.mac_address
    ).first()

    agora = datetime.now(timezone.utc)

    if equipamento:
        # Atualiza dados e último contato
        equipamento.serial = payload.serial or equipamento.serial
        equipamento.hostname = payload.hostname
        equipamento.sistema_operacional = payload.sistema_operacional
        equipamento.cpu = payload.cpu
        equipamento.ram = payload.ram
        equipamento.discos = payload.discos
        equipamento.gpus = payload.gpus
        equipamento.ultimo_contato = agora
    else:
        equipamento = Equipamento(
            **payload.model_dump(),
            criado_em=agora,
            ultimo_contato=agora,
        )
        db.add(equipamento)

    db.commit()
    db.refresh(equipamento)
    return equipamento


@router.get("", response_model=list[EquipamentoOut])
def listar_equipamentos(db: Session = Depends(get_db)):
    return db.query(Equipamento).order_by(Equipamento.id).all()


@router.get("/{equipamento_id}", response_model=EquipamentoOut)
def buscar_equipamento(equipamento_id: int, db: Session = Depends(get_db)):
    eq = db.query(Equipamento).filter(Equipamento.id == equipamento_id).first()
    if not eq:
        raise HTTPException(status_code=404, detail="Equipamento não encontrado.")
    return eq


@router.get("/{equipamento_id}/job-pendente", response_model=JobOut)
def job_pendente(equipamento_id: int, db: Session = Depends(get_db)):
    """
    Agent faz polling aqui. Retorna o job PENDENTE mais antigo
    para este equipamento, ou 204 se não houver nenhum.
    """
    job = db.query(Job).filter(
        Job.equipamento_id == equipamento_id,
        Job.status == "PENDENTE",
    ).order_by(Job.criado_em).first()

    if not job:
        raise HTTPException(status_code=204, detail="Sem job pendente.")

    return job