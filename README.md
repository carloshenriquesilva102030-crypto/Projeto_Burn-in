# Burn-in Agent

Agent Python que roda nos equipamentos sob teste.

## Arquivos

```
agent/
├── main.py         # ponto de entrada — roda aqui
├── collector.py    # coleta MAC, serial, CPU, RAM, SSD, GPU
├── stress.py       # executa os testes e monitora em tempo real
├── reporter.py     # toda comunicação com a API central
└── requirements.txt
```

## Dependências do sistema (Ubuntu)

```bash
sudo apt install stress-ng fio smartmontools
# GPU (opcional):
# gpu-burn: https://github.com/wilicc/gpu-burn
```

## Instalação do Python

```bash
pip install -r requirements.txt
```

## Como rodar

```bash
# Apontando para a API central
python main.py --api http://IP_DO_SERVIDOR:8000

# Com intervalo de métricas menor (ex: a cada 10s)
python main.py --api http://IP_DO_SERVIDOR:8000 --intervalo 10
```

## Testar o collector isolado

```bash
python collector.py
```

Vai imprimir o hardware detectado em JSON — útil para verificar se o MAC,
serial e demais informações estão sendo capturados corretamente.

## Fluxo completo

```
main.py
  │
  ├─ collector.collect()           → pega MAC, serial, CPU, RAM, SSD, GPU
  ├─ api.registrar_equipamento()   → POST /equipamentos
  ├─ api.aguardar_job()            → GET /equipamentos/{id}/job-pendente (polling)
  ├─ api.iniciar_job()             → POST /jobs/{id}/iniciar
  │
  ├─ stress.executar()             → loop pelo tempo configurado (4h/8h/12h/24h)
  │     ├─ stress-ng CPU
  │     ├─ stress-ng RAM
  │     ├─ fio SSD
  │     ├─ gpu_burn (se disponível)
  │     ├─ a cada 30s: coletar_metricas_snapshot()
  │     │     ├─ api.enviar_metrica()   → POST /jobs/{id}/metricas
  │     │     └─ verificar temperatura, SMART
  │     └─ ao detectar falha crítica: api.enviar_evento()
  │
  └─ api.finalizar_job()           → POST /jobs/{id}/finalizar
```

## Regras de falha

| Condição                        | Tipo de evento        | Efeito              |
|---------------------------------|-----------------------|---------------------|
| Temperatura CPU ≥ 90 °C         | TEMPERATURA_ALTA      | Alerta (não para)   |
| Atributo SMART crítico > 0      | SMART_FAIL            | Reprovação imediata |
| Processo de stress morto        | EXECUCAO              | Alerta + registro   |
| Agent sem resposta (API)        | AGENTE_SEM_RESPOSTA   | Detectado pela API  |
