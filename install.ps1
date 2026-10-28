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

  if ($env:ZEUG_PROJECT_SETUP -eq '1') {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) { $python = Get-Command python3 -ErrorAction SilentlyContinue }
    if (-not $python) { throw 'Project setup requires Python 3.9 or newer; use the project download after installing Python.' }
    $tmp = Join-Path ([IO.Path]::GetTempPath()) ([guid]::NewGuid().ToString())
    New-Item -ItemType Directory -Path $tmp | Out-Null
    try {
      $profile = Invoke-RestMethod -Uri "$api/api/agent/setup" -Headers @{ Authorization = "Bearer $key" }
      [IO.File]::WriteAllText((Join-Path $tmp 'project.json'), ($profile | ConvertTo-Json -Depth 10), (New-Object Text.UTF8Encoding $false))
      Invoke-WebRequest -UseBasicParsing -Uri "$repo/collaborator/kit.json" -OutFile (Join-Path $tmp 'kit.json')
      $kit = Get-Content -Raw (Join-Path $tmp 'kit.json') | ConvertFrom-Json
      $script = [string]$kit.files.'setup.py'
      $sha = [Security.Cryptography.SHA256]::Create()
      $hash = -join ($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($script)) | ForEach-Object { $_.ToString('x2') })
      if ($hash -ne $kit.sha256.'setup.py') { throw 'Invalid setup checksum' }
      [IO.File]::WriteAllText((Join-Path $tmp 'setup.py'), $script, (New-Object Text.UTF8Encoding $false))
      $target = if ($env:ZEUG_PROJECT_DIR) { $env:ZEUG_PROJECT_DIR } else { Join-Path $PWD $project }
      & $python.Source (Join-Path $tmp 'setup.py') init --kit (Join-Path $tmp 'kit.json') --profile (Join-Path $tmp 'project.json') --target $target
      if ($LASTEXITCODE -ne 0) { throw 'Project setup failed; existing files were preserved. Follow the error above.' }
    } finally { Remove-Item -Recurse -Force $tmp }
    $env:ZEUG_KEY = $null
    Write-Host 'Project setup is ready. Your existing global skills and saved keys were not changed. Sign in with your own accounts.'
    return
  }


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
  # Lock the file down while it is still empty, then write the key into it.
  Set-Content -Path $file -Value '' -NoNewline
  if ($env:OS -eq 'Windows_NT') {
    icacls $file /inheritance:r /grant:r "${env:USERNAME}:(R,W)" | Out-Null
    if ($LASTEXITCODE -ne 0) { Remove-Item -Force $file; throw "Could not restrict $file to your account." }
  } else {
    chmod 700 $conf
    chmod 600 $file
  }
  # LF line endings and no BOM, so Git Bash and WSL can read the same file.
  [IO.File]::WriteAllText($file, "ZEUG_PROJECT=$project`nZEUG_MEMORY_KEY=$key`nZEUG_API=$api`n", (New-Object Text.UTF8Encoding $false))
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
