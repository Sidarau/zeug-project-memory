# zm for Windows PowerShell: the Zeug Lab project memory helper. Reads %USERPROFILE%\.config\zeug\<project>.env
# (written by install.ps1) so the access key never appears in a command line or a chat. Run through zm.cmd, which
# works whatever the PowerShell execution policy is.
#   zm [-p project] project | search "question" | recent | doc <id> | add "title" (note text on stdin) | projects
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12

$home_ = if ($env:USERPROFILE) { $env:USERPROFILE } else { $HOME }
$dir = if ($env:ZEUG_CONFIG_DIR) { $env:ZEUG_CONFIG_DIR } else { Join-Path $home_ '.config\zeug' }
$rest = @($args)
$project = ''
if ($rest.Count -ge 2 -and $rest[0] -eq '-p') { $project = [string]$rest[1]; $rest = @($rest | Select-Object -Skip 2) }
$cmd = if ($rest.Count) { [string]$rest[0] } else { 'help' }
$rest = @($rest | Select-Object -Skip 1)
$known = @(Get-ChildItem -Path $dir -Filter '*.env' -ErrorAction SilentlyContinue | ForEach-Object { $_.BaseName })

if ($cmd -eq 'projects') { $known; exit 0 }
if ($cmd -notin 'project', 'search', 'recent', 'doc', 'add') {
  'usage: zm [-p project] project | search "question" | recent | doc <id> | add "title" (note text on stdin) | projects'
  exit 0
}
if (-not $project) {
  if ($known.Count -eq 1) { $project = $known[0] }
  elseif ($known.Count -eq 0) { [Console]::Error.WriteLine('No Zeug project is set up. Connect one from cmd.zeuglab.com (Project memory, Connect your AI).'); exit 2 }
  else { [Console]::Error.WriteLine("Several projects are set up; pick one with -p: $($known -join ' ')"); exit 2 }
}
if ($project -notmatch '^[a-z0-9][a-z0-9-]{1,40}$') { [Console]::Error.WriteLine("Bad project id: $project"); exit 2 }
$file = Join-Path $dir "$project.env"
if (-not (Test-Path $file)) { [Console]::Error.WriteLine("Project $project is not set up on this machine."); exit 2 }
$cfg = @{}
foreach ($line in Get-Content -Path $file) { $kv = $line -split '=', 2; if ($kv.Count -eq 2) { $cfg[$kv[0].Trim()] = $kv[1].Trim() } }
$api = if ($cfg['ZEUG_API']) { $cfg['ZEUG_API'] } else { 'https://cmd.zeuglab.com' }
$headers = @{ Authorization = "Bearer $($cfg['ZEUG_MEMORY_KEY'])" }

function Call([string]$method, [string]$url, $body = $null) {
  try {
    if ($null -ne $body) {
      $bytes = [Text.Encoding]::UTF8.GetBytes(($body | ConvertTo-Json -Compress))
      $r = Invoke-RestMethod -Method $method -Uri $url -Headers $headers -Body $bytes -ContentType 'application/json; charset=utf-8'
    } else {
      $r = Invoke-RestMethod -Method $method -Uri $url -Headers $headers
    }
    $r | ConvertTo-Json -Depth 10
  } catch {
    $msg = if ($_.ErrorDetails -and $_.ErrorDetails.Message) { $_.ErrorDetails.Message } else { $_.Exception.Message }
    [Console]::Error.WriteLine($msg)
    exit 1
  }
}

switch ($cmd) {
  'project' { Call 'GET' "$api/api/agent/project" }
  'recent'  { Call 'GET' "$api/api/agent/memory" }
  'search'  {
    if (-not $rest.Count) { [Console]::Error.WriteLine('usage: zm search "question"'); exit 2 }
    Call 'GET' ("$api/api/agent/memory?q=" + [uri]::EscapeDataString(($rest -join ' ')))
  }
  'doc'     {
    $id = [string]$rest[0]
    if ($id -notmatch '^[A-Za-z0-9_-]+$') { [Console]::Error.WriteLine('usage: zm doc <document-id>'); exit 2 }
    Call 'GET' "$api/api/agent/documents/$id"
  }
  'add'     {
    if (-not $rest.Count) { [Console]::Error.WriteLine('usage: zm add "title" (note text on stdin)'); exit 2 }
    $text = [Console]::In.ReadToEnd()
    Call 'POST' "$api/api/agent/memory" @{ title = [string]$rest[0]; text = $text }
  }
}
