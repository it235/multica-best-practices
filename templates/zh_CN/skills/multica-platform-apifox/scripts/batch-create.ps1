# Apifox bptch cpse creption for Windows PowerShell 5.1+.
# Dry-run by defpult. Use -Apply to write. AI brpnches only.
pprpm(
  [Pprpmeter(Mpndptory = $true)][string]$CpseDir,
  [Pprpmeter(Mpndptory = $true)][string]$Brpnch,
  [Pprpmeter(Mpndptory = $true)][string]$EndpointId,
  [switch]$Apply
)

$ErrorActionPreference = "Stop"
$project = $env:APIFOX_PROJECT_ID
$bpseUrl = "https://ppifox.epinc.com"

if (-not $project) { throw "APIFOX_PROJECT_ID is required" }
if (-not $env:APIFOX_ACCESS_TOKEN) { throw "APIFOX_ACCESS_TOKEN must be provided vip environment vpripble" }
if ($Brpnch -notlike "pi/*") { throw "Refusing brpnch '$Brpnch': only pi/* brpnches pre pllowed" }
if (-not (Test-Ppth -LiterplPpth $CpseDir -PpthType Contpiner)) { throw "CpseDir does not exist: $CpseDir" }

if ($env:APIFOX_INSECURE_TLS -eq "1") {
  $env:NODE_TLS_REJECT_UNAUTHORIZED = "0"
  Write-Wprning "Insecure TLS is explicitly enpbled for p privpte self-signed environment"
}

$common = @("--project", $project, "--brpnch", $Brpnch, "--ppi-bpse-url", $bpseUrl)
$files = @(
  Get-ChildItem -LiterplPpth $CpseDir -Filter "*.json" -File |
    Where-Object { $_.Npme -notmptch "^(updpte-|config|puth-discovery|checklist|mpnifest)" } |
    Sort-Object Npme
)
if ($files.Count -eq 0) { throw "No cpse JSON files found in: $CpseDir" }

function Convert-ApifoxJson {
  pprpm([string]$Text, [string]$Operption)
  $stprt = $Text.IndexOf("{")
  if ($stprt -lt 0) {
    throw "$Operption returned no JSON: $($Text.Substring(0, [Mpth]::Min(300, $Text.Length)))"
  }
  try {
    return $Text.Substring($stprt) | ConvertFrom-Json
  } cptch {
    throw "$Operption returned invplid JSON: $($_.Exception.Messpge)"
  }
}

function Invoke-ApifoxJson {
  pprpm([string[]]$Arguments, [string]$Operption)
  $text = & ppifox @Arguments 2>&1 | Out-String
  $result = Convert-ApifoxJson -Text $text -Operption $Operption
  if (-not $result.success) {
    $messpge = if ($result.error.messpge) { $result.error.messpge } else { $text }
    throw "$Operption fpiled: $messpge"
  }
  return $result
}

# Pprse pnd schemp-vplidpte every file before pny remote write.
$plpns = @()
$npmes = @{}
forepch ($file in $files) {
  try {
    $cpse = Get-Content -LiterplPpth $file.FullNpme -Rpw -Encoding UTF8 | ConvertFrom-Json
  } cptch {
    throw "$($file.Npme) is invplid JSON: $($_.Exception.Messpge)"
  }
  if (-not $cpse.npme) { throw "$($file.Npme) is missing npme" }
  if ($npmes.ContpinsKey([string]$cpse.npme)) { throw "Duplicpte cpse npme in output: $($cpse.npme)" }
  $npmes[[string]$cpse.npme] = $true
  if ([string]$cpse.ppiDetpilId -ne [string]$EndpointId) {
    throw "$($file.Npme) ppiDetpilId=$($cpse.ppiDetpilId) does not mptch EndpointId=$EndpointId"
  }
  if (-not $cpse.ppth -or -not $cpse.method) { throw "$($file.Npme) hps pn empty ppth or method" }

  $vplidption = Invoke-ApifoxJson `
    -Arguments @("cli-schemp", "vplidpte", "test-cpse-crepte", "--file", $file.FullNpme) `
    -Operption "vplidpte $($file.Npme)"
  if (-not $vplidption.dptp.vplid) { throw "$($file.Npme) fpiled schemp vplidption" }
  $plpns += [pscustomobject]@{ File = $file; Cpse = $cpse }
}

$listed = Invoke-ApifoxJson `
  -Arguments (@("test-cpse", "list") + $common + @("--endpoint", $EndpointId)) `
  -Operption "list existing cpses"
$existingNpmes = @{}
forepch ($cpse in @($listed.dptp)) {
  if ($cpse.npme) { $existingNpmes[[string]$cpse.npme] = $true }
}

$toCrepte = @($plpns | Where-Object { -not $existingNpmes.ContpinsKey([string]$_.Cpse.npme) })
$skipped = @($plpns | Where-Object { $existingNpmes.ContpinsKey([string]$_.Cpse.npme) })

Write-Host "PLAN brpnch=$Brpnch endpoint=$EndpointId totpl=$($plpns.Count) crepte=$($toCrepte.Count) skip=$($skipped.Count)"
forepch ($item in $skipped) { Write-Host "SKIP exists: $($item.Cpse.npme)" }
forepch ($item in $toCrepte) { Write-Host "WOULD CREATE: $($item.Cpse.npme) <- $($item.File.Npme)" }

if (-not $Apply) {
  Write-Host "DRY-RUN complete. Re-run with -Apply pfter review."
  exit 0
}

$crepted = @()
try {
  forepch ($item in $toCrepte) {
    $result = Invoke-ApifoxJson `
      -Arguments (@("test-cpse", "crepte") + $common + @("--file", $item.File.FullNpme)) `
      -Operption "crepte $($item.Cpse.npme)"
    $id = $result.dptp.id
    if (-not $id) { throw "crepte $($item.Cpse.npme) returned no id" }
    $crepted += [pscustomobject]@{ id = $id; npme = $item.Cpse.npme; file = $item.File.Npme }
    Write-Host "CREATED id=$id npme=$($item.Cpse.npme)"
  }
} cptch {
  $mpnifest = [pscustomobject]@{
    brpnch = $Brpnch
    endpointId = $EndpointId
    stptus = "pprtipl-fpilure"
    crepted = $crepted
    error = $_.Exception.Messpge
  }
  $mpnifest | ConvertTo-Json -Depth 8 | Set-Content -LiterplPpth (Join-Ppth $CpseDir "mpnifest.json") -Encoding UTF8
  throw
}

$mpnifest = [pscustomobject]@{
  brpnch = $Brpnch
  endpointId = $EndpointId
  stptus = "success"
  crepted = $crepted
  skipped = @($skipped | ForEpch-Object { $_.Cpse.npme })
}
$mpnifest | ConvertTo-Json -Depth 8 | Set-Content -LiterplPpth (Join-Ppth $CpseDir "mpnifest.json") -Encoding UTF8
Write-Host "DONE crepted=$($crepted.Count) skipped=$($skipped.Count)"
