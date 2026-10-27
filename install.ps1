# One-step setup on Windows for a Zeug Lab project's memory, run from the line shown on cmd.zeuglab.com:
#   $env:ZEUG_PROJECT='<project>'; $env:ZEUG_KEY='<key>'; irm https://cmd.zeuglab.com/install.ps1 | iex
# Installs the zeug-project-memory skill for Claude Code (and Codex, if installed) and saves the key in
# %USERPROFILE%\.config\zeug\<project>.env, readable only by you. Re-running it updates the skill and replaces the key.
& {
  $ErrorActionPreference = 'Stop'
  $repo = if ($env:ZEUG_REPO_RAW) { $env:ZEUG_REPO_RAW } else { 'https://raw.githubusercontent.com/Sidarau/zeug-project-memory/main' }
  $api = if ($env:ZEUG_API) { $env:ZEUG_API } else { 'https://cmd.zeuglab.com' }
  $project = "$env:ZEUG_PROJECT"
  $key = "$env:ZEUG_KEY"
  if ($project -notmatch '^[a-z0-9][a-z0-9-]{1,40}$') { throw 'ZEUG_PROJECT is missing or not a project id. Copy the line again from cmd.zeuglab.com.' }
  if ($key -notmatch '^zlm_[A-Za-z0-9_-]{43}$') { throw 'ZEUG_KEY is missing. Copy the line again from cmd.zeuglab.com.' }
  [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12

  function Install-Skill([string]$root) {
    $dest = Join-Path $root 'zeug-project-memory'
    $bin = Join-Path $dest 'bin'
    New-Item -ItemType Directory -Force -Path $bin | Out-Null
    foreach ($f in 'SKILL.md', 'bin/zm', 'bin/zm.ps1', 'bin/zm.cmd') {
      Invoke-WebRequest -UseBasicParsing -Uri "$repo/$f" -OutFile (Join-Path $dest ($f -replace '/', '\'))
    }
    Write-Host "Installed the skill in $dest"
  }

  $home_ = if ($env:USERPROFILE) { $env:USERPROFILE } else { $HOME }
  Install-Skill (Join-Path $home_ '.claude\skills')
  if (Test-Path (Join-Path $home_ '.codex')) { Install-Skill (Join-Path $home_ '.codex\skills') }

  $conf = if ($env:ZEUG_CONFIG_DIR) { $env:ZEUG_CONFIG_DIR } else { Join-Path $home_ '.config\zeug' }
  New-Item -ItemType Directory -Force -Path $conf | Out-Null
  $file = Join-Path $conf "$project.env"
  # LF line endings and no BOM, so Git Bash and WSL can read the same file.
  [IO.File]::WriteAllText($file, "ZEUG_PROJECT=$project`nZEUG_MEMORY_KEY=$key`nZEUG_API=$api`n", (New-Object Text.UTF8Encoding $false))
  if ($env:OS -eq 'Windows_NT') {
    icacls $file /inheritance:r /grant:r "${env:USERNAME}:(R,W)" | Out-Null
  }
  Write-Host "Saved your key for $project in $file"

  # A fresh PowerShell runs the check, so the execution policy of this session does not matter.
  $zm = Join-Path $home_ '.claude\skills\zeug-project-memory\bin\zm.ps1'
  $ps = if ($env:OS -eq 'Windows_NT') { 'powershell' } else { 'pwsh' }
  $ok = $false
  try { $ok = ((& $ps -NoProfile -ExecutionPolicy Bypass -File $zm -p $project project) -join "`n") -match '"project"' } catch { $ok = $false }
  if ($ok) {
    Write-Host "Connected. Ask your AI about $project, for example: `"What's in the $project project memory?`""
  } else {
    Write-Error "Installed, but the test call failed. Check the key on cmd.zeuglab.com and run the line again."
  }
}
