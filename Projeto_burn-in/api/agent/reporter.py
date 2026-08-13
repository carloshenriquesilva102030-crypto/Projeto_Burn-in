"""
reporter.py
Toda a comunicação do agent com a API central.
"""

import time
import requests
from stress import Evento, ResultadoBurnIn


class APIClient:
    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def _post(self, path: str, payload: dict) -> dict:
        url = f"{self.base_url}{path}"
        for tentativa in range(3):
            try:
                resp = self.session.post(url, json=payload, timeout=self.timeout)
                resp.raise_for_status()
                return resp.json()
            except requests.RequestException as e:
                print(f"[API] Erro em POST {path} (tentativa {tentativa + 1}/3): {e}")
                if tentativa < 2:
                    time.sleep(5)
        raise RuntimeError(f"Falha ao chamar {path} após 3 tentativas.")

    # Registro do equipamento

    def registrar_equipamento(self, hardware_info: dict) -> int:
        """
        Registra (ou atualiza) o equipamento na API.
        Retorna o equipamento_id.
        """
        resp = self._post("/equipamentos", hardware_info)
        return resp["id"]

    # Job de burn-in

    def aguardar_job(self, equipamento_id: int, poll_intervalo_s: int = 10) -> dict:
        """
        Faz polling na API até receber um job pendente para este equipamento.
        Retorna o dict do job: { id, duracao_horas, ... }
        """
        url = f"{self.base_url}/equipamentos/{equipamento_id}/job-pendente"
        print(f"[Agent] Aguardando job para equipamento {equipamento_id}...")
        while True:
            try:
                resp = self.session.get(url, timeout=self.timeout)
                if resp.status_code == 200:
                    job = resp.json()
                    print(f"[Agent] Job recebido: ID={job['id']}, duração={job['duracao_horas']}h")
                    return job
                elif resp.status_code == 204:
                    pass  # sem job pendente, continua aguardando
            except requests.RequestException as e:
                print(f"[Agent] Erro ao buscar job: {e}")
            time.sleep(poll_intervalo_s)

    def iniciar_job(self, job_id: int) -> None:
        self._post(f"/jobs/{job_id}/iniciar", {})

    # Métricas durante execução

    def enviar_metrica(self, job_id: int, metricas: dict) -> None:
        """Envia um snapshot de métricas. Falhas são logadas, não bloqueiam."""
        try:
            self._post(f"/jobs/{job_id}/metricas", metricas)
        except RuntimeError as e:
            print(f"[Reporter] Falha ao enviar métricas: {e}")

    def enviar_evento(self, job_id: int, evento: Evento) -> None:
        payload = {
            "tipo": evento.tipo,
            "descricao": evento.descricao,
            "timestamp": evento.timestamp,
            "critico": evento.critico,
        }
        try:
            self._post(f"/jobs/{job_id}/eventos", payload)
        except RuntimeError as e:
            print(f"[Reporter] Falha ao enviar evento: {e}")

    # Finalização do job

    def finalizar_job(self, job_id: int, resultado: ResultadoBurnIn) -> None:
        payload = {
            "aprovado": resultado.aprovado,
            "duracao_real_segundos": resultado.duracao_real_segundos,
            "motivo_reprovacao": resultado.motivo_reprovacao,
            "total_eventos": len(resultado.eventos),
        }
        self._post(f"/jobs/{job_id}/finalizar", payload)
        status = "APROVADO ✓" if resultado.aprovado else "REPROVADO ✗"
        print(f"[Agent] Job {job_id} finalizado: {status}")