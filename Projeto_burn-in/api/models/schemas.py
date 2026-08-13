"""
schemas.py
Modelos Pydantic — validação de entrada e saída da API.
"""

from pydantic import BaseModel
from typing import Any
from datetime import datetime


# ---------------------------------------------------------------------------
# Equipamento
# ---------------------------------------------------------------------------

class EquipamentoIn(BaseModel):
    mac_address: str
    serial: str | None = None
    hostname: str | None = None
    sistema_operacional: str | None = None
    cpu: dict | None = None
    ram: dict | None = None
    discos: list[dict] | None = None
    gpus: list[dict] | None = None


class EquipamentoOut(BaseModel):
    id: int
    mac_address: str
    serial: str | None
    hostname: str | None
    sistema_operacional: str | None
    cpu: dict | None
    ram: dict | None
    discos: list | None
    gpus: list | None
    criado_em: datetime
    ultimo_contato: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Job
# ---------------------------------------------------------------------------

class JobCreate(BaseModel):
    equipamento_id: int
    duracao_horas: int  # 4 | 8 | 12 | 24


class JobOut(BaseModel):
    id: int
    equipamento_id: int
    duracao_horas: int
    status: str
    iniciado_em: datetime | None
    finalizado_em: datetime | None
    aprovado: bool | None
    motivo_reprovacao: str | None
    criado_em: datetime

    model_config = {"from_attributes": True}


class JobFinalizar(BaseModel):
    aprovado: bool
    duracao_real_segundos: float
    motivo_reprovacao: str | None = None
    total_eventos: int = 0


# ---------------------------------------------------------------------------
# Métricas
# ---------------------------------------------------------------------------

class MetricaIn(BaseModel):
    timestamp: float
    cpu_percent: float | None = None
    ram_percent: float | None = None
    ram_usado_gb: float | None = None
    temperaturas: dict[str, float] | None = None


class MetricaOut(BaseModel):
    id: int
    job_id: int
    timestamp: float
    cpu_percent: float | None
    ram_percent: float | None
    ram_usado_gb: float | None
    temperaturas: dict | None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Eventos
# ---------------------------------------------------------------------------

class EventoIn(BaseModel):
    tipo: str
    descricao: str
    timestamp: float
    critico: bool = False


class EventoOut(BaseModel):
    id: int
    job_id: int
    tipo: str
    descricao: str
    timestamp: float
    critico: bool

    model_config = {"from_attributes": True}