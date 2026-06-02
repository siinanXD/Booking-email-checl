# Graph-Verbindungstest: Token + 3 Mails aus INBOX.
# Nutzung (im Projektroot):
#   .\.venv\Scripts\Activate.ps1
#   .\scripts\test_graph_mailbox.ps1
#
# Liest AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, OUTLOOK_MAILBOX aus .env

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$envFile = Join-Path $root ".env"

if (-not (Test-Path $envFile)) {
    Write-Error ".env nicht gefunden: $envFile"
}

function Normalize-EnvValue([string]$raw) {
    $v = $raw.Trim()
    # Anführungszeichen und Platzhalter-Klammern aus Anleitungen entfernen
    if (
        ($v.StartsWith('"') -and $v.EndsWith('"')) -or
        ($v.StartsWith("'") -and $v.EndsWith("'"))
    ) {
        $v = $v.Substring(1, $v.Length - 2)
    }
    if ($v.StartsWith('<') -and $v.EndsWith('>')) {
        $v = $v.Substring(1, $v.Length - 2).Trim()
    }
    return $v
}

$loadedKeys = @()
Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
        $name = $matches[1].Trim()
        $value = Normalize-EnvValue $matches[2]
        if ($value -ne "") {
            Set-Item -Path "Env:$name" -Value $value
            $loadedKeys += $name
        }
    }
}
Write-Host ("Aus .env geladen: " + ($loadedKeys -join ", "))

$required = @(
    "AZURE_TENANT_ID",
    "AZURE_CLIENT_ID",
    "AZURE_CLIENT_SECRET",
    "OUTLOOK_MAILBOX"
)
foreach ($key in $required) {
    $value = [Environment]::GetEnvironmentVariable($key, "Process")
    if (-not $value) {
        Write-Error "$key fehlt oder ist leer in .env"
    }
}

$tenant = [Environment]::GetEnvironmentVariable("AZURE_TENANT_ID", "Process")
$client = [Environment]::GetEnvironmentVariable("AZURE_CLIENT_ID", "Process")
$secret = [Environment]::GetEnvironmentVariable("AZURE_CLIENT_SECRET", "Process")
$mailbox = [Environment]::GetEnvironmentVariable("OUTLOOK_MAILBOX", "Process")

if ($tenant -notmatch '^[0-9a-fA-F-]{36}$') {
    Write-Error "AZURE_TENANT_ID sieht ungültig aus (GUID aus Entra > Übersicht > Verzeichnis-ID)."
}
if ($client -notmatch '^[0-9a-fA-F-]{36}$') {
    Write-Error "AZURE_CLIENT_ID sieht ungültig aus (GUID aus Entra > Übersicht > Anwendungs-ID)."
}

Write-Host "Tenant/Client/Mailbox geladen. Secret wird nicht ausgegeben."
Write-Host "OUTLOOK_MAILBOX=$mailbox"

$tokenBody = @{
    client_id     = $client
    client_secret = $secret
    scope         = "https://graph.microsoft.com/.default"
    grant_type    = "client_credentials"
}

try {
    $tokenResp = Invoke-RestMethod -Method Post `
        -Uri "https://login.microsoftonline.com/$tenant/oauth2/v2.0/token" `
        -Body $tokenBody
    Write-Host "Token: OK"
}
catch {
    Write-Host "Token FEHLER: $($_.Exception.Message)"
    if ($_.ErrorDetails.Message) { Write-Host $_.ErrorDetails.Message }
    Write-Host ""
    Write-Host "Bei 404: AZURE_TENANT_ID leer/falsch oder .env nicht geladen."
    Write-Host "Bei invalid_client: AZURE_CLIENT_SECRET falsch oder abgelaufen."
    exit 1
}

$headers = @{ Authorization = "Bearer $($tokenResp.access_token)" }
$uri = "https://graph.microsoft.com/v1.0/users/$mailbox/mailFolders/inbox/messages?`$top=3&`$select=subject,from,receivedDateTime"

try {
    $mails = Invoke-RestMethod -Headers $headers -Uri $uri
    Write-Host "Mailbox: $mailbox"
    Write-Host "Mails abgerufen: $($mails.value.Count)"
    foreach ($m in $mails.value) {
        $from = $m.from.emailAddress.address
        Write-Host "  - [$($m.receivedDateTime)] $($m.subject) (von: $from)"
    }
    if ($mails.value.Count -eq 0) {
        Write-Host "Hinweis: INBOX ist leer oder Zugriff ohne sichtbare Mails."
    }
}
catch {
    Write-Host "Graph FEHLER: $($_.Exception.Message)"
    if ($_.ErrorDetails.Message) { Write-Host $_.ErrorDetails.Message }
    Write-Host ""
    Write-Host "Typische Ursachen:"
    Write-Host "  - OUTLOOK_MAILBOX falsch (SMTP des Shared Postfachs)"
    Write-Host "  - App hat kein Recht auf dieses Postfach (Exchange Application Access Policy)"
    Write-Host "  - Mail.Read nur Delegated statt Application"
    exit 1
}
