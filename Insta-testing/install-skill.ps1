# =====================================================================
#  Install "instaprotek-regression-testing" as a PROJECT skill for
#  Claude Code (loads when you work in the pm-instaprotek project and
#  its subfolders). Also removes any old PERSONAL-scope copy.
#
#  Run once in Tabby (Command Prompt or PowerShell):
#     powershell -ExecutionPolicy Bypass -File "C:\Users\sarahgamba\Dropbox\PC\Documents\pm-instaprotek\Insta-testing\install-skill.ps1"
#
#  $projectRoot = the folder you open Claude Code in. Change it if yours differs.
# =====================================================================
$ErrorActionPreference = 'Stop'

$src         = 'C:\Users\sarahgamba\Dropbox\PC\Documents\pm-instaprotek\Insta-testing\instaprotek-regression-testing.skill'
$projectRoot = 'C:\Users\sarahgamba\Dropbox\PC\Documents\pm-instaprotek'
$dest        = Join-Path $projectRoot '.claude\skills'
$tmp         = Join-Path $env:TEMP 'irt-skill.zip'
$target      = Join-Path $dest 'instaprotek-regression-testing'
$personal    = Join-Path $env:USERPROFILE '.claude\skills\instaprotek-regression-testing'

if (-not (Test-Path $src)) { throw "Cannot find skill bundle at $src" }

# 1) Remove the old PERSONAL-scope copy so there is no duplicate skill
if (Test-Path $personal) {
    Remove-Item $personal -Recurse -Force
    Write-Host "Removed personal-scope copy: $personal"
}

# 2) Install as a PROJECT skill
Write-Host "Installing project skill from:`n  $src"
Copy-Item $src $tmp -Force                                     # Expand-Archive requires a .zip extension
New-Item -ItemType Directory -Force $dest | Out-Null
if (Test-Path $target) { Remove-Item $target -Recurse -Force } # clean reinstall
Expand-Archive -Path $tmp -DestinationPath $dest -Force
Remove-Item $tmp -Force

Write-Host "`nInstalled to:`n  $target`n"
Get-ChildItem -Recurse $target | Select-Object -ExpandProperty FullName
Write-Host "`nDone. Restart Claude Code from $projectRoot, then run:  /instaprotek-regression-testing"
