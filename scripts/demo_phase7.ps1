# OpsPilot Phase 7 Demo — Backend happy path (no frontend).
# Prerequisite: docker compose up (postgres + backend healthy)
# Usage:  .\scripts\demo_phase7.ps1
# Optional: .\scripts\demo_phase7.ps1 -BaseUrl http://localhost:8080

[CmdletBinding()]
param(
    [string]$BaseUrl = "http://localhost:8080"
)

$ErrorActionPreference = "Stop"
$BaseUrl = $BaseUrl.TrimEnd("/")

function Write-Step {
    param([string]$Title)
    Write-Host ""
    Write-Host "=== $Title ===" -ForegroundColor Cyan
}

function Invoke-Api {
    param(
        [Parameter(Mandatory = $true)][ValidateSet("GET", "POST", "PATCH")][string]$Method,
        [Parameter(Mandatory = $true)][string]$Path,
        [string]$Token,
        [hashtable]$Body
    )

    $uri = "$BaseUrl$Path"
    $headers = @{ Accept = "application/json" }
    if ($Token) {
        $headers["Authorization"] = "Bearer $Token"
    }

    $params = @{
        Method      = $Method
        Uri         = $uri
        Headers     = $headers
        ContentType = "application/json"
    }
    if ($PSBoundParameters.ContainsKey("Body")) {
        if ($null -eq $Body) {
            $params["Body"] = "{}"
        }
        else {
            $params["Body"] = ($Body | ConvertTo-Json -Compress -Depth 6)
        }
    }

    try {
        $resp = Invoke-RestMethod @params
    }
    catch {
        $detail = $_.Exception.Message
        if ($_.ErrorDetails -and $_.ErrorDetails.Message) {
            $detail = $_.ErrorDetails.Message
        }
        throw "API $Method $Path failed: $detail"
    }

    return $resp
}

function Assert-BizOk {
    param(
        [Parameter(Mandatory = $true)]$Response,
        [string]$Context
    )
    if ($null -eq $Response) {
        throw "$Context : empty response"
    }
    if ($null -ne $Response.code -and [int]$Response.code -ne 0) {
        throw "$Context : business code=$($Response.code) message=$($Response.message)"
    }
}

Write-Host "OpsPilot Phase 7 Demo"
Write-Host "BaseUrl = $BaseUrl"

# ---------------------------------------------------------------------------
# 1. Health
# ---------------------------------------------------------------------------
Write-Step "1. GET /health"
$health = Invoke-Api -Method GET -Path "/health"
$health | ConvertTo-Json -Depth 5 | Write-Host
if ($health.status -notin @("ok", "degraded")) {
    throw "health status unexpected: $($health.status)"
}
Write-Host "OK: health.status=$($health.status) database=$($health.database)"

# ---------------------------------------------------------------------------
# 2. Employee login
# ---------------------------------------------------------------------------
Write-Step "2. Employee login (demo@opspilot.local)"
$empLogin = Invoke-Api -Method POST -Path "/api/v1/auth/login" -Body @{
    username = "demo@opspilot.local"
    password = "password123"
}
Assert-BizOk $empLogin "Employee login"
$EmpToken = [string]$empLogin.data.token
if ([string]::IsNullOrWhiteSpace($EmpToken)) {
    throw "Employee login: missing token"
}
Write-Host "OK: employee token acquired (len=$($EmpToken.Length)) user=$($empLogin.data.user.username) role=$($empLogin.data.user.role)"

# ---------------------------------------------------------------------------
# 3. Create Ticket
# ---------------------------------------------------------------------------
Write-Step "3. Employee create Ticket"
$ticketCreate = Invoke-Api -Method POST -Path "/api/v1/tickets" -Token $EmpToken -Body @{
    title       = "Phase7 Demo: VPN cannot connect"
    description = "Demo ticket created by scripts/demo_phase7.ps1"
    priority    = "high"
}
Assert-BizOk $ticketCreate "Create ticket"
$TicketId = [string]$ticketCreate.data.id
if ([string]::IsNullOrWhiteSpace($TicketId)) {
    throw "Create ticket: missing id"
}
Write-Host "OK: ticket id=$TicketId status=$($ticketCreate.data.status)"

# ---------------------------------------------------------------------------
# 4. Support login
# ---------------------------------------------------------------------------
Write-Step "4. Support login (support@opspilot.local)"
$supLogin = Invoke-Api -Method POST -Path "/api/v1/auth/login" -Body @{
    username = "support@opspilot.local"
    password = "password123"
}
Assert-BizOk $supLogin "Support login"
$SupToken = [string]$supLogin.data.token
if ([string]::IsNullOrWhiteSpace($SupToken)) {
    throw "Support login: missing token"
}
Write-Host "OK: support token acquired (len=$($SupToken.Length)) user=$($supLogin.data.user.username) role=$($supLogin.data.user.role)"

# ---------------------------------------------------------------------------
# 5. Get Ticket
# ---------------------------------------------------------------------------
Write-Step "5. Support GET Ticket"
$ticketGet = Invoke-Api -Method GET -Path "/api/v1/tickets/$TicketId" -Token $SupToken
Assert-BizOk $ticketGet "Get ticket"
Write-Host ($ticketGet.data | ConvertTo-Json -Depth 6)
Write-Host "OK: ticket status=$($ticketGet.data.status)"

# ---------------------------------------------------------------------------
# 6. Advance status: assigned → in_progress → resolved → closed
# ---------------------------------------------------------------------------
Write-Step "6. Support advance Ticket status"
$statusChain = @("assigned", "in_progress", "resolved", "closed")
foreach ($status in $statusChain) {
    $patched = Invoke-Api -Method PATCH -Path "/api/v1/tickets/$TicketId" -Token $SupToken -Body @{
        status = $status
    }
    Assert-BizOk $patched "PATCH status=$status"
    Write-Host "OK: -> $($patched.data.status) (requested=$status)"
    if ([string]$patched.data.status -ne $status) {
        throw "status mismatch: expected=$status got=$($patched.data.status)"
    }
}

# ---------------------------------------------------------------------------
# 7. Employee create Permission (real fields)
# ---------------------------------------------------------------------------
Write-Step "7. Employee create Permission"
$permCreate = Invoke-Api -Method POST -Path "/api/v1/permissions" -Token $EmpToken -Body @{
    resource_type     = "GITLAB"
    resource_name     = "ops/demo-repo"
    permission_level  = "READ"
    reason            = "Phase7 demo: need read access to demo repo"
}
Assert-BizOk $permCreate "Create permission"
$PermId = [string]$permCreate.data.id
if ([string]::IsNullOrWhiteSpace($PermId)) {
    throw "Create permission: missing id"
}
Write-Host "OK: permission id=$PermId status=$($permCreate.data.status)"

# ---------------------------------------------------------------------------
# 8. Support approve Permission
# ---------------------------------------------------------------------------
Write-Step "8. Support approve Permission"
$permApprove = Invoke-Api -Method POST -Path "/api/v1/permissions/$PermId/approve" -Token $SupToken
Assert-BizOk $permApprove "Approve permission"
Write-Host "OK: permission id=$($permApprove.data.id) status=$($permApprove.data.status)"
if ([string]$permApprove.data.status -ne "approved") {
    throw "approve expected status=approved got=$($permApprove.data.status)"
}

# ---------------------------------------------------------------------------
# 9. Audit acceptance SQL (no Audit HTTP API)
# ---------------------------------------------------------------------------
Write-Step "9. Audit acceptance SQL (run manually)"
Write-Host @"
# Expect SUCCESS rows for this demo run, including at least:
#   ticket.create / ticket.update / access_request.create / access_request.approve
#
# Option A — docker compose:
docker compose exec -T postgres psql -U opspilot -d opspilot -c "SELECT created_at, action, resource_type, resource_id, result FROM audit_logs WHERE resource_id IN ('$TicketId', '$PermId') OR action IN ('ticket.create','ticket.update','access_request.create','access_request.approve') ORDER BY created_at DESC LIMIT 30;"

# Option B — local psql (if port mapped):
psql "postgres://opspilot:opspilot@localhost:5432/opspilot?sslmode=disable" -c "SELECT created_at, action, resource_type, resource_id, result FROM audit_logs ORDER BY created_at DESC LIMIT 30;"

# Narrow to this demo's resources:
#   ticket_id      = $TicketId
#   permission_id  = $PermId
"@

Write-Host ""
Write-Host "=== Phase 7 demo HTTP path PASSED ===" -ForegroundColor Green
Write-Host "TicketId=$TicketId  PermId=$PermId"
Write-Host "Next: run the Audit SQL above to verify Phase 6 Lite write-path."
