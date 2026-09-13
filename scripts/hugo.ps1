param(
	[switch]$Serve,
	[Parameter(ValueFromRemainingArguments = $true)]
	[string[]]$HugoArguments
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$version = (Get-Content -LiteralPath (Join-Path $projectRoot '.hugo-version') -Raw).Trim()
if ($version -notmatch '^\d+\.\d+\.\d+$') { throw 'Invalid .hugo-version.' }
$architecture = if ($env:PROCESSOR_ARCHITECTURE -eq 'ARM64') { 'arm64' } else { 'amd64' }
$toolsDirectory = Join-Path $projectRoot ".tools/hugo/$version/$architecture"
$hugoExecutable = Join-Path $toolsDirectory 'hugo.exe'

if (-not (Test-Path -LiteralPath $hugoExecutable)) {
	New-Item -ItemType Directory -Force -Path $toolsDirectory | Out-Null
	$archiveName = "hugo_${version}_windows-$architecture.zip"
	$releaseUrl = "https://github.com/gohugoio/hugo/releases/download/v$version"
	$archivePath = Join-Path $toolsDirectory $archiveName
	$checksumsPath = Join-Path $toolsDirectory 'checksums.txt'
	Write-Host "Downloading Hugo $version ($architecture)..."
	[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
	Invoke-WebRequest "$releaseUrl/$archiveName" -OutFile $archivePath -UseBasicParsing
	Invoke-WebRequest "$releaseUrl/hugo_${version}_checksums.txt" -OutFile $checksumsPath -UseBasicParsing
	$checksumLine = Get-Content -LiteralPath $checksumsPath | Where-Object { $_.EndsWith(" $archiveName") }
	if (-not $checksumLine) { throw 'Hugo archive checksum not found.' }
	$expectedHash = ($checksumLine -split '\s+')[0]
	$hashAlgorithm = [Security.Cryptography.SHA256]::Create()
	$archiveStream = [IO.File]::OpenRead($archivePath)
	try {
		$actualHash = [BitConverter]::ToString($hashAlgorithm.ComputeHash($archiveStream)).Replace('-', '')
	} finally {
		$archiveStream.Dispose()
		$hashAlgorithm.Dispose()
	}
	if ($actualHash -ine $expectedHash) {
		throw 'Hugo download checksum mismatch.'
	}
	Add-Type -AssemblyName System.IO.Compression.FileSystem
	$archive = [IO.Compression.ZipFile]::OpenRead($archivePath)
	try {
		$executableEntry = $archive.Entries | Where-Object { $_.FullName -eq 'hugo.exe' }
		if (-not $executableEntry) { throw 'Hugo executable not found in archive.' }
		[IO.Compression.ZipFileExtensions]::ExtractToFile($executableEntry, $hugoExecutable, $true)
	} finally {
		$archive.Dispose()
	}
}

Push-Location $projectRoot
try {
	if ($Serve) {
		& $hugoExecutable server --bind 127.0.0.1 --port 1313 --destination .tools/preview --buildDrafts @HugoArguments
	} else {
		& $hugoExecutable --minify --destination public @HugoArguments
	}
	$hugoExitCode = $LASTEXITCODE
} finally {
	Pop-Location
}
exit $hugoExitCode
