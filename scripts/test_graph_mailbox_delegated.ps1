# Graph test: private mailbox (Hotmail/Outlook) via delegated device code.
# Usage: .\scripts\test_graph_mailbox_delegated.ps1
# Requires in Entra: personal accounts allowed, public client flows, Mail.Read (Delegated).

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$envFile = Join-Path $root ".env"

function Normalize-EnvValue {
    param([string]$Raw)
    $v = $Raw.Trim()
    if (($v.StartsWith('"') -and $v.EndsWith('"')) -or ($v.StartsWith("'") -and $v.EndsWith("'"))) {
        $v = $v.Substring(1, $v.Length - 2)
    }
    if ($v.StartsWith('<') -and $v.EndsWith('>')) {
        $v = $v.Substring(1, $v.Length - 2).Trim()
    }
    return $v
}

if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = Normalize-EnvValue $matches[2]
            if ($value -ne "") {
                Set-Item -Path "Env:$name" -Value $value
            }
        }
    }
}

$clientId = [Environment]::GetEnvironmentVariable("AZURE_CLIENT_ID", "Process")
if (-not $clientId) {
    throw "AZURE_CLIENT_ID fehlt in .env"
}

$tenant = [Environment]::GetEnvironmentVariable("AZURE_AUTHORITY", "Process")
if (-not $tenant) {
    # "common" = privat + Firmen; bei 401 mit consumers: AZURE_AUTHORITY=common in .env
    $tenant = "common"
}

$scope = @(
    "openid"
    "profile"
    "offline_access"
    "https://graph.microsoft.com/User.Read"
    "https://graph.microsoft.com/Mail.Read"
) -join " "
$deviceUri = "https://login.microsoftonline.com/$tenant/oauth2/v2.0/devicecode"
$tokenUri = "https://login.microsoftonline.com/$tenant/oauth2/v2.0/token"

Write-Host "Delegated Device Code (Authority: $tenant)"
Write-Host "Client-ID geladen."

$device = Invoke-RestMethod -Method Post -Uri $deviceUri -Body @{
    client_id = $clientId
    scope     = $scope
}

Write-Host ""
Write-Host $device.message
Write-Host ""
Write-Host "WICHTIG: Terminal offen lassen bis 'Token: OK' erscheint (nach Browser-Anmeldung)."
Write-Host ""

$deadline = (Get-Date).AddSeconds([int]$device.expires_in)
$token = $null
$pollSeconds = [int]$device.interval
if ($pollSeconds -lt 5) {
    $pollSeconds = 5
}

while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds $pollSeconds
    try {
        $tokenResp = Invoke-RestMethod -Method Post -Uri $tokenUri -Body @{
            grant_type  = "urn:ietf:params:oauth:grant-type:device_code"
            client_id   = $clientId
            device_code = $device.device_code
        }
        $token = $tokenResp.access_token
        break
    }
    catch {
        $errJson = $_.ErrorDetails.Message
        $err = $null
        if ($errJson) {
            $err = $errJson | ConvertFrom-Json -ErrorAction SilentlyContinue
        }
        if ($err -and $err.error -eq "authorization_pending") {
            continue
        }
        if ($err -and $err.error -eq "authorization_declined") {
            throw "Anmeldung abgelehnt."
        }
        $code = if ($err) { $err.error } else { "unknown" }
        $desc = if ($err) { $err.error_description } else { $_.Exception.Message }
        throw "Token FEHLER: $code - $desc"
    }
}

if (-not $token) {
    throw "Zeit abgelaufen - Device Code nicht bestaetigt."
}

Write-Host "Token: OK (delegated)"

# Scopes im Token anzeigen (ohne Secret auszugeben)
try {
    $payload = $token.Split(".")[1]
    $pad = "=" * ((4 - ($payload.Length % 4)) % 4)
    $json = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($payload + $pad))
    $claims = $json | ConvertFrom-Json
    if ($claims.scp) {
        Write-Host "Token-Scopes: $($claims.scp)"
    }
    if ($claims.aud) {
        Write-Host "Token-Audience: $($claims.aud)"
    }
}
catch {
    Write-Host "Token-Scopes: (konnte nicht gelesen werden)"
}

$headers = @{ Authorization = "Bearer $token" }
$mailUri = "https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messages?`$top=3&`$select=subject,from,receivedDateTime"

try {
    $me = Invoke-RestMethod -Headers $headers -Uri "https://graph.microsoft.com/v1.0/me?`$select=mail,userPrincipalName,displayName"
    Write-Host "Angemeldet als: $($me.userPrincipalName) ($($me.displayName))"
    if ($me.mail) {
        Write-Host "mail-Feld: $($me.mail)"
    }

    Write-Host ""
    Write-Host "Postfach-Ordner (totalItemCount):"
    $folders = Invoke-RestMethod -Headers $headers -Uri "https://graph.microsoft.com/v1.0/me/mailFolders?`$top=25&`$select=id,displayName,totalItemCount,unreadItemCount"
    foreach ($f in $folders.value) {
        Write-Host ("  - {0}: {1} gesamt, {2} ungelesen" -f $f.displayName, $f.totalItemCount, $f.unreadItemCount)
    }

    $inbox = ($folders.value | Where-Object { $_.displayName -match 'Inbox|Posteingang' } | Select-Object -First 1)
    if ($inbox -and $inbox.totalItemCount -gt 0) {
        $mailUri = "https://graph.microsoft.com/v1.0/me/mailFolders/$($inbox.id)/messages?`$top=5&`$select=subject,from,receivedDateTime"
    }

    $mails = Invoke-RestMethod -Headers $headers -Uri $mailUri
    Write-Host ""
    Write-Host "Mails aus INBOX (API): $($mails.value.Count)"
    foreach ($m in $mails.value) {
        $from = $m.from.emailAddress.address
        Write-Host "  - [$($m.receivedDateTime)] $($m.subject) (von: $from)"
    }

    if ($mails.value.Count -eq 0) {
        Write-Host ""
        Write-Host "Keine Mails in INBOX ueber Graph - Versuch alle Ordner (/me/messages):"
        $all = Invoke-RestMethod -Headers $headers -Uri "https://graph.microsoft.com/v1.0/me/messages?`$top=5&`$select=subject,from,receivedDateTime,parentFolderId"
        Write-Host "Mails (/me/messages): $($all.value.Count)"
        foreach ($m in $all.value) {
            $from = $m.from.emailAddress.address
            Write-Host "  - [$($m.receivedDateTime)] $($m.subject) (von: $from)"
        }
        if ($all.value.Count -eq 0) {
            Write-Host ""
            Write-Host "Moegliche Ursachen:"
            Write-Host "  1) Skript mit Strg+C beendet BEVOR 'Token: OK' kam"
            Write-Host "  2) Anderes Konto im Browser als erwartet angemeldet"
            Write-Host "  3) Postfach wirklich leer (Outlook im Web pruefen)"
            Write-Host "  4) Mail.Read (Delegated) nicht zugestimmt"
            Write-Host "  5) https://account.live.com/consent/Manage - App-Zugriff pruefen"
        }
    }
}
catch {
    Write-Host "Graph FEHLER: $($_.Exception.Message)"
    if ($_.ErrorDetails.Message) {
        Write-Host $_.ErrorDetails.Message
    }
    Write-Host ""
    Write-Host "Pruefen:"
    Write-Host "  - Mail.Read UND User.Read (beide Delegated) + Zustimmung"
    Write-Host "  - Skript erneut starten und ALLE Berechtigungen im Browser bestaetigen"
    Write-Host "  - Persoenliche Konten + oeffentliche Clientflows in Entra"
    exit 1
}
