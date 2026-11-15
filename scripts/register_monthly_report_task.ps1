$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
$reportScript = Join-Path $PSScriptRoot "generate_monthly_report.py"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Python do ambiente virtual não encontrado: $python"
}

$action = New-ScheduledTaskAction `
    -Execute $python `
    -Argument "`"$reportScript`"" `
    -WorkingDirectory $projectRoot
$trigger = New-ScheduledTaskTrigger -Daily -At 11:55PM
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 10)
$task = New-ScheduledTask -Action $action -Trigger $trigger -Principal $principal -Settings $settings `
    -Description "Gera e armazena o relatório financeiro no último dia de cada mês."
Register-ScheduledTask -TaskName "FinancialManagerMonthlyReport" -InputObject $task -Force | Out-Null
Write-Output "Agendamento diário configurado. O script só gera relatório no último dia do mês."
