$maxSizeMB = 100
$maxSizeBytes = $maxSizeMB * 1024 * 1024

# 1. Identify modified/untracked files using Git, which respects .gitignore
$stagedFiles = git diff --name-only --cached --diff-filter=ACMR
$unstagedFiles = git diff --name-only --diff-filter=ACMR
$untrackedFiles = git ls-files --others --exclude-standard

$allFilePaths = ($stagedFiles + $unstagedFiles + $untrackedFiles) | Sort-Object -Unique

$allChangedFiles = $allFilePaths | ForEach-Object {
    # Get-Item can fail if a file was deleted since we got the list
    Get-Item $_ -ErrorAction SilentlyContinue
} | Where-Object { $_ } # Filter out nulls from failed Get-Item

# 2. Process large files
$largeFiles = $allChangedFiles | Where-Object { $_.Length -gt $maxSizeBytes }

foreach ($file in $largeFiles) {
    $relativePath = Resolve-Path -Path $file.FullName -Relative
    $archivePath = "$($file.FullName).7z"
    
    Write-Host "Processing large modified file: $($file.Name)" -ForegroundColor Cyan
    
    # --- FIX STARTS HERE ---
    # Remove existing volumes to avoid the "Updating not implemented" error
    Write-Host "Cleaning up old volumes..." -DarkGray
    Remove-Item "$archivePath.*" -ErrorAction SilentlyContinue
    # --- FIX ENDS HERE ---
    
    # Split into 7z volumes
    & 7z a -v"$($maxSizeMB)m" $archivePath $file.FullName
    
    # Add the generated volumes to git
    git add "$($relativePath).7z.*"
    
    # Ensure the original large file is not staged
    git restore --staged $relativePath 2>$null
}

# 3. Add all other changed files (smaller than the limit)
$smallFiles = $allChangedFiles | Where-Object { $_.Length -le $maxSizeBytes }

foreach ($file in $smallFiles) {
    $rel = Resolve-Path -Path $file.FullName -Relative
    git add $rel
}

Write-Host "Done! Large files split and smaller changes staged, bro." -ForegroundColor Green