param(
    [Parameter(Mandatory=$true)][string]$InputDocx,
    [Parameter(Mandatory=$true)][string]$OutputPdf
)
$ErrorActionPreference = 'Stop'
$sourceRevision = (Resolve-Path -LiteralPath $InputDocx).Path
$destinationRevision = [System.IO.Path]::GetFullPath($OutputPdf)
$wordRevision = New-Object -ComObject Word.Application
$wordRevision.Visible = $false
$wordRevision.DisplayAlerts = 0
$documentRevision = $null
try {
    $documentRevision = $wordRevision.Documents.Open($sourceRevision,$false,$true)
    $documentRevision.ExportAsFixedFormat($destinationRevision,17)
    Write-Output "Rendered: $destinationRevision"
    Write-Output "Pages: $($documentRevision.ComputeStatistics(2))"
}
finally {
    if ($null -ne $documentRevision) { $documentRevision.Close(0) }
    $wordRevision.Quit()
}
