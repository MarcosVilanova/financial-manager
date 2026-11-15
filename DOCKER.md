# Executar com Docker

Requer Docker Desktop com suporte ao Docker Compose.

Na pasta do projeto, execute:

```powershell
docker compose up --build -d
```

Abra <http://localhost:8501>. O Compose copia o banco local para o volume nomeado na primeira execução, sem sobrescrever um volume já inicializado. Depois, a interface Streamlit e o serviço agendador compartilham esse banco persistente. As alterações feitas no Docker ficam no volume e não são sincronizadas de volta ao `financial_manager.db` local.

Comandos úteis:

```powershell
docker compose logs -f app report-scheduler
docker compose down
```

`docker compose down` preserva os dados. `docker compose down -v` remove também o volume e apaga o banco usado no Docker.

O arquivo `financial_manager.db` local não é copiado para a imagem. Um serviço de inicialização lê esse arquivo uma vez e cria a cópia inicial no volume. Se quiser começar com um banco vazio, renomeie ou remova o arquivo local antes da primeira execução do Compose.
