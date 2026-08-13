"""
main.py
Ponto de entrada do Burn-in Agent.

Uso:
    python main.py --api http://192.168.1.100:8000

O agent:
  1. Coleta o hardware da máquina
  2. Registra na API
  3. Aguarda um job de burn-in ser atribuído
  4. Executa os testes (CPU, RAM, SSD, GPU)
  5. Envia métricas e eventos em tempo real
  6. Finaliza reportando APROVADO ou REPROVADO
"""

import argparse
import json
import sys

import collector
import stress
from reporter import APIClient


def main():
    parser = argparse.ArgumentParser(description="Burn-in Agent")
    parser.add_argument(
        "--api",
        default="http://localhost:8000",
        help="URL base da API central (ex: http://192.168.1.100:8000)",
    )
    parser.add_argument(
        "--intervalo",
        type=int,
        default=30,
        help="Intervalo em segundos entre coletas de métricas (padrão: 30)",
    )
    args = parser.parse_args()

    api = APIClient(base_url=args.api)

    # ------------------------------------------------------------------ #
    # 1. Coleta de hardware
    # ------------------------------------------------------------------ #
    print("[Agent] Coletando informações de hardware...")
    hardware = collector.collect()
    print(json.dumps(hardware, indent=2, ensure_ascii=False))

    # ------------------------------------------------------------------ #
    # 2. Registro na API
    # ------------------------------------------------------------------ #
    try:
        equipamento_id = api.registrar_equipamento(hardware)
        print(f"[Agent] Equipamento registrado. ID={equipamento_id}")
    except RuntimeError as e:
        print(f"[Agent] ERRO: não foi possível registrar na API: {e}")
        sys.exit(1)

    # ------------------------------------------------------------------ #
    # 3. Aguarda job
    # ------------------------------------------------------------------ #
    job = api.aguardar_job(equipamento_id)
    job_id = job["id"]
    duracao_horas = job["duracao_horas"]

    api.iniciar_job(job_id)

    # ------------------------------------------------------------------ #
    # 4 + 5. Execução dos testes com coleta em tempo real
    # ------------------------------------------------------------------ #
    def ao_receber_metrica(metricas: dict):
        api.enviar_metrica(job_id, metricas)

    def ao_receber_evento(evento: stress.Evento):
        print(f"[Evento] {evento.tipo}: {evento.descricao}")
        api.enviar_evento(job_id, evento)

    resultado = stress.executar(
        duracao_horas=duracao_horas,
        job_id=job_id,
        on_metrica=ao_receber_metrica,
        on_evento=ao_receber_evento,
        intervalo_metricas_s=args.intervalo,
    )

    # ------------------------------------------------------------------ #
    # 6. Finalização
    # ------------------------------------------------------------------ #
    api.finalizar_job(job_id, resultado)


if __name__ == "__main__":
    main()