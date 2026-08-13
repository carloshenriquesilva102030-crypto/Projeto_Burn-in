"""
database.py
Conexão com o PostgreSQL e definição das tabelas via SQLAlchemy.
"""

import os
from sqlalchemy import (
    create_engine, Column, Integer, String, Float,
    Boolean, DateTime, ForeignKey, Text, JSON
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime, timezone

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://burnin:burnin@localhost:5432/burnin"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


# ---------------------------------------------------------------------------
# Tabelas
# ---------------------------------------------------------------------------

class Equipamento(Base):
    __tablename__ = "equipamentos"

    id              = Column(Integer, primary_key=True, index=True)
    mac_address     = Column(String, unique=True, nullable=False, index=True)
    serial          = Column(String, nullable=True)
    hostname        = Column(String, nullable=True)
    sistema_operacional = Column(String, nullable=True)
    cpu             = Column(JSON, nullable=True)   # { modelo, nucleos_fisicos, ... }
    ram             = Column(JSON, nullable=True)   # { total_gb }
    discos          = Column(JSON, nullable=True)   # [ { dispositivo, total_gb, ... } ]
    gpus            = Column(JSON, nullable=True)   # [ { modelo, memoria } ] | null
    criado_em       = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    ultimo_contato  = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    jobs = relationship("Job", back_populates="equipamento")


class Job(Base):
    __tablename__ = "jobs"

    id              = Column(Integer, primary_key=True, index=True)
    equipamento_id  = Column(Integer, ForeignKey("equipamentos.id"), nullable=False)
    duracao_horas   = Column(Integer, nullable=False)   # 4 | 8 | 12 | 24
    status          = Column(String, default="PENDENTE") # PENDENTE | EM_EXECUCAO | APROVADO | REPROVADO
    iniciado_em     = Column(DateTime, nullable=True)
    finalizado_em   = Column(DateTime, nullable=True)
    duracao_real_segundos = Column(Float, nullable=True)
    aprovado        = Column(Boolean, nullable=True)
    motivo_reprovacao = Column(Text, nullable=True)
    criado_em       = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    equipamento = relationship("Equipamento", back_populates="jobs")
    metricas    = relationship("Metrica", back_populates="job")
    eventos     = relationship("Evento", back_populates="job")


class Metrica(Base):
    __tablename__ = "metricas"

    id              = Column(Integer, primary_key=True, index=True)
    job_id          = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    timestamp       = Column(Float, nullable=False)
    cpu_percent     = Column(Float, nullable=True)
    ram_percent     = Column(Float, nullable=True)
    ram_usado_gb    = Column(Float, nullable=True)
    temperaturas    = Column(JSON, nullable=True)   # { "sensor": valor_celsius }

    job = relationship("Job", back_populates="metricas")


class Evento(Base):
    __tablename__ = "eventos"

    id          = Column(Integer, primary_key=True, index=True)
    job_id      = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    tipo        = Column(String, nullable=False)    # TEMPERATURA_ALTA | SMART_FAIL | ...
    descricao   = Column(Text, nullable=False)
    timestamp   = Column(Float, nullable=False)
    critico     = Column(Boolean, default=False)

    job = relationship("Job", back_populates="eventos")


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------

def get_db():
    """Dependency do FastAPI para injetar sessão do banco."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def criar_tabelas():
    Base.metadata.create_all(bind=engine)