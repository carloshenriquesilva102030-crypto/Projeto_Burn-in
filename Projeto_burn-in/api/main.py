"""
main.py
Ponto de entrada da API Burn-in.
"""

from fastapi import FastAPI
from database import criar_tabelas
from routes import equipamentos, jobs, metricas

app = FastAPI(
    title="Burn-in API",
    description="API central do sistema de burn-in de equipamentos.",
    version="1.0.0",
)


@app.on_event("startup")
def startup():
    criar_tabelas()


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(equipamentos.router, prefix="/equipamentos", tags=["Equipamentos"])
app.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
app.include_router(metricas.router, prefix="/jobs", tags=["Métricas e Eventos"])