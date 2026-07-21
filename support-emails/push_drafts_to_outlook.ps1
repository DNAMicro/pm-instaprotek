# =====================================================================
#  Push InstaProtek support draft replies into your Outlook Drafts.
#  Creates DRAFTS ONLY - it never sends.
#
#  Drafts land in the signed-in profile's Drafts folder (your admin
#  account), each with From = support@instaprotek.com (you have Send As),
#  so you can open, confirm, and send them from the support address.
#
#  Requirements: classic Outlook for Windows (desktop), signed in.
#  (Does NOT work with "new Outlook" or Outlook on the web - no COM.)
#
#  Run in PowerShell:
#   powershell -ExecutionPolicy Bypass -File ".\push_drafts_to_outlook.ps1"
# =====================================================================
$ErrorActionPreference = 'Stop'
$DraftsDir = Join-Path $PSScriptRoot 'drafts'
$Support   = 'support@instaprotek.com'

$ol = New-Object -ComObject Outlook.Application
$ns = $ol.GetNamespace('MAPI')
$target = $ns.GetDefaultFolder(16)   # 16 = olFolderDrafts (admin's Drafts)

$files = Get-ChildItem -Path $DraftsDir -Filter *.md | Where-Object { $_.Name -ne 'README.md' }
$made = 0
foreach ($f in $files) {
    $txt = Get-Content $f.FullName -Raw
    $parts = $txt -split 'READY-TO-PASTE REPLY[^\r\n]*-->'
    if ($parts.Count -lt 2) { Write-Host "skip (no reply marker): $($f.Name)"; continue }
    $reply = $parts[1]

    $to=$null; $subj=$null; $bodyLines=@(); $inBody=$false
    foreach ($ln in ($reply -split "`r?`n")) {
        if ($inBody) { $bodyLines += $ln; continue }
        if ($ln -match '^\*\*To:\*\*\s*(.+)$')     { $to   = $Matches[1].Trim(); continue }
        if ($ln -match '^\*\*Subject:\*\*\s*(.+)$') { $subj = $Matches[1].Trim(); $inBody = $true; continue }
    }
    if (-not $to -or -not $subj) { Write-Host "skip (no To/Subject): $($f.Name)"; continue }
    $body = ($bodyLines -join "`r`n").Trim()

    $mail = $ol.CreateItem(0)                 # olMailItem
    $mail.To = $to
    $mail.Subject = $subj
    $mail.Body = $body
    try { $mail.SentOnBehalfOfName = $Support } catch { }
    $mail.Save()                              # DRAFT only - never .Send()
    if ($target) { [void]$mail.Move($target) }
    $made++
    Write-Host "draft created: $to  |  $subj"
}
Write-Host "`nDone. $made draft(s) in your Outlook Drafts, From support@instaprotek.com. Review and send from Outlook."
