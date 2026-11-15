# Agendamento do relatório mensal (Windows)

O relatório é idempotente por mês: a execução diária só gera um relatório quando hoje é o último dia do mês e atualiza o resumo daquele mês. Os dados ficam na tabela `monthly_reports`; o PDF pode ser baixado pela tela **Relatórios**.

No PowerShell, a partir da pasta do projeto, execute uma vez:

```powershell
 powershell -ExecutionPolicy Bypass -File .\scripts\register_monthly_report_task.ps1
```

O agendador executa às 23:55 usando o Python de `.venv`. A tarefa roda quando a conta do Windows está conectada. Se a execução do último dia for perdida, a próxima execução diária gera o relatório do mês anterior como recuperação.

Para executar manualmente:

```powershell
.\.venv\Scripts\python.exe .\scripts\generate_monthly_report.py
```
