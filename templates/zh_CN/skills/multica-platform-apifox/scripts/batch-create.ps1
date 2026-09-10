# Apifox batch case creation for Windows PowerShell 5.1+.
# Dry-run by default. Use -Apply to write. AI branches only.
param(
  [Parameter(Mandatory = $true)][string]$CaseDir,
  [Parameter(Mandatory = $true)][string]$Branch,
  [Parameter(Mandatory = $true)][string]$EndpointId,
  [switch]$Apply
)

$ErrorActionPreference = "Stop"
$project = $env:APIFOX_PROJECT_ID
$baseUrl = "https://apifox.example.com"

if (-not $project) { throw "APIFOX_PROJECT_ID is required" }
if (-not $env:APIFOX_ACCESS_TOKEN) { throw "APIFOX_ACCESS_TOKEN must be provided via environment variable" }
if ($Branch -notlike "ai/*") { throw "Refusing branch '$Branch': only ai/* branches are allowed" }
if (-not (Test-Path -LiteralPath $CaseDir -PathType Container)) { throw "CaseDir does not exist: $CaseDir" }

if ($env:APIFOX_INSECURE_TLS -eq "1") {
  $env:NODE_TLS_REJECT_UNAUTHORIZED = "0"
  Write-Warning "Insecure TLS is explicitly enabled for a private self-signed environment"
}

$common = @("--project", $project, "--branch", $Branch, "--api-base-url", $baseUrl)
$files = @(
  Get-ChildItem -LiteralPath $CaseDir -Filter "*.json" -File |
    Where-Object { $_.Name -notmatch "^(update-|config|auth-discovery|checklist|manifest)" } |
    Sort-Object Name
)
if ($files.Count -eq 0) { throw "No case JSON files found in: $CaseDir" }

function Convert-ApifoxJson {
  param([string]$Text, [string]$Operation)
  $start = $Text.IndexOf("{")
  if ($start -lt 0) {
    throw "$Operation returned no JSON: $($Text.Substring(0, [Math]::Min(300, $Text.Length)))"
  }
  try {
    return $Text.Substring($start) | ConvertFrom-Json
  } catch {
    throw "$Operation returned invalid JSON: $($_.Exception.Message)"
  }
}

function Invoke-ApifoxJson {
  param([string[]]$Arguments, [string]$Operation)
  $text = & apifox @Arguments 2>&1 | Out-String
  $result = Convert-ApifoxJson -Text $text -Operation $Operation
  if (-not $result.success) {
    $message = if ($result.error.message) { $result.error.message } else { $text }
    throw "$Operation failed: $message"
  }
  return $result
}

# Parse and schema-validate every file before any remote write.
$plans = @()
$names = @{}
foreach ($file in $files) {
  try {
    $case = Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
  } catch {
    throw "$($file.Name) is invalid JSON: $($_.Exception.Message)"
  }
  if (-not $case.name) { throw "$($file.Name) is missing name" }
  if ($names.ContainsKey([string]$case.name)) { throw "Duplicate case name in output: $($case.name)" }
  $names[[string]$case.name] = $true
  if ([string]$case.apiDetailId -ne [string]$EndpointId) {
    throw "$($file.Name) apiDetailId=$($case.apiDetailId) does not match EndpointId=$EndpointId"
  }
  if (-not $case.path -or -not $case.method) { throw "$($file.Name) has an empty path or method" }

  $validation = Invoke-ApifoxJson `
    -Arguments @("cli-schema", "validate", "test-case-create", "--file", $file.FullName) `
    -Operation "validate $($file.Name)"
  if (-not $validation.data.valid) { throw "$($file.Name) failed schema validation" }
  $plans += [pscustomobject]@{ File = $file; Case = $case }
}

$listed = Invoke-ApifoxJson `
  -Arguments (@("test-case", "list") + $common + @("--endpoint", $EndpointId)) `
  -Operation "list existing cases"
$existingNames = @{}
foreach ($case in @($listed.data)) {
  if ($case.name) { $existingNames[[string]$case.name] = $true }
}

$toCreate = @($plans | Where-Object { -not $existingNames.ContainsKey([string]$_.Case.name) })
$skipped = @($plans | Where-Object { $existingNames.ContainsKey([string]$_.Case.name) })

Write-Host "PLAN branch=$Branch endpoint=$EndpointId total=$($plans.Count) create=$($toCreate.Count) skip=$($skipped.Count)"
foreach ($item in $skipped) { Write-Host "SKIP exists: $($item.Case.name)" }
foreach ($item in $toCreate) { Write-Host "WOULD CREATE: $($item.Case.name) <- $($item.File.Name)" }

if (-not $Apply) {
  Write-Host "DRY-RUN complete. Re-run with -Apply after review."
  exit 0
}

$created = @()
try {
  foreach ($item in $toCreate) {
    $result = Invoke-ApifoxJson `
      -Arguments (@("test-case", "create") + $common + @("--file", $item.File.FullName)) `
      -Operation "create $($item.Case.name)"
    $id = $result.data.id
    if (-not $id) { throw "create $($item.Case.name) returned no id" }
    $created += [pscustomobject]@{ id = $id; name = $item.Case.name; file = $item.File.Name }
    Write-Host "CREATED id=$id name=$($item.Case.name)"
  }
} catch {
  $manifest = [pscustomobject]@{
    branch = $Branch
    endpointId = $EndpointId
    status = "partial-failure"
    created = $created
    error = $_.Exception.Message
  }
  $manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $CaseDir "manifest.json") -Encoding UTF8
  throw
}

$manifest = [pscustomobject]@{
  branch = $Branch
  endpointId = $EndpointId
  status = "success"
  created = $created
  skipped = @($skipped | ForEach-Object { $_.Case.name })
}
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $CaseDir "manifest.json") -Encoding UTF8
Write-Host "DONE created=$($created.Count) skipped=$($skipped.Count)"
