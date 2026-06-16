
# ============================================================
# commit_all_files.ps1
# Creates one individual commit per changed/untracked file
# with a meaningful commit message, then pushes all to GitHub.
# ============================================================

Set-Location "d:\Downloads\Github\Ai-Assistant"

Write-Host "=== Individual File Commit Script ===" -ForegroundColor Cyan
Write-Host "Collecting all changed and untracked files..." -ForegroundColor Yellow

# Get every individual file (including inside untracked dirs)
$files = git status --porcelain -u | ForEach-Object {
    $status = $_.Substring(0,2).Trim()
    $filePath = $_.Substring(3).Trim()
    # Handle renamed files (format: "old -> new")
    if ($filePath -match ' -> ') {
        $filePath = ($filePath -split ' -> ')[1]
    }
    [PSCustomObject]@{ Status = $status; File = $filePath }
}

$total = $files.Count
Write-Host "Found $total files to commit." -ForegroundColor Green
Write-Host ""

$count = 0
foreach ($item in $files) {
    $count++
    $file = $item.File
    $status = $item.Status

    # --- Build a meaningful commit message based on status and file type ---
    $ext = [System.IO.Path]::GetExtension($file).ToLower()
    $name = [System.IO.Path]::GetFileName($file)
    $dir  = [System.IO.Path]::GetDirectoryName($file)

    # Determine action verb
    $action = switch ($status) {
        "M"  { "Update" }
        "A"  { "Add" }
        "D"  { "Remove" }
        "R"  { "Rename" }
        "C"  { "Copy" }
        "??" { "Add" }
        default { "Track" }
    }

    # Determine file category for richer messages
    $category = switch -Wildcard ($ext) {
        ".py"     { "Python module" }
        ".js"     { "JavaScript module" }
        ".jsx"    { "React component" }
        ".ts"     { "TypeScript module" }
        ".tsx"    { "React TypeScript component" }
        ".css"    { "stylesheet" }
        ".html"   { "HTML template" }
        ".json"   { "JSON configuration" }
        ".yml"    { "YAML configuration" }
        ".yaml"   { "YAML configuration" }
        ".md"     { "documentation" }
        ".txt"    { "text file" }
        ".ps1"    { "PowerShell script" }
        ".sh"     { "shell script" }
        ".bat"    { "batch script" }
        ".dll"    { "DLL library" }
        ".exe"    { "executable binary" }
        ".env"    { "environment config" }
        ".spec"   { "build spec file" }
        ".cfg"    { "configuration file" }
        ".ini"    { "configuration file" }
        ".toml"   { "TOML configuration" }
        ".xml"    { "XML file" }
        ".svg"    { "SVG asset" }
        ".png"    { "image asset" }
        ".jpg"    { "image asset" }
        ".ico"    { "icon asset" }
        ".woff"   { "web font" }
        ".woff2"  { "web font" }
        ".ttf"    { "font file" }
        default   { "file" }
    }

    # Contextual detail based on file name / path
    $detail = ""
    if ($file -match "backend-dist") {
        if ($ext -eq ".dll")  { $detail = ": package compiled Windows dependency for portable backend" }
        elseif ($ext -eq ".exe") { $detail = ": include compiled backend executable for distribution" }
        else                  { $detail = ": include compiled backend distribution asset" }
    } elseif ($file -match "agent\.py")          { $detail = ": enhance AI agent logic and tool integration" }
    elseif ($file -match "main_agent\.py")        { $detail = ": refactor main agent entry point and orchestration" }
    elseif ($file -match "server\.py")            { $detail = ": improve FastAPI server routes and middleware" }
    elseif ($file -match "vector_memory\.py")     { $detail = ": optimise vector memory storage and retrieval" }
    elseif ($file -match "App\.jsx")              { $detail = ": update Electron renderer UI and component layout" }
    elseif ($file -match "main\.css|assets.*css") { $detail = ": refine global styles and theme variables" }
    elseif ($file -match "index\.js")             { $detail = ": update Electron main process configuration" }
    elseif ($file -match "package\.json")         { $detail = ": bump dependencies and update build scripts" }
    elseif ($file -match "electron-builder")      { $detail = ": configure Electron Builder packaging options" }
    elseif ($file -match "requirements\.txt")     { $detail = ": update Python package requirements" }
    elseif ($file -match "build_backend")         { $detail = ": add PowerShell build script for backend packaging" }
    elseif ($file -match "\.env")                 { $detail = ": update environment variable template" }

    $commitMsg = "${action} ${category} '${name}'${detail}"

    Write-Host "[$count/$total] Committing: $file" -ForegroundColor White
    Write-Host "  Message: $commitMsg" -ForegroundColor DarkGray

    # Stage only this file
    git add -- $file 2>&1 | Out-Null

    # Commit with meaningful message
    $result = git commit -m $commitMsg 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  WARNING: Commit failed for $file" -ForegroundColor Red
        Write-Host "  $result" -ForegroundColor DarkRed
    } else {
        Write-Host "  OK" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "=== All $total commits created! ===" -ForegroundColor Cyan
Write-Host "Pushing all commits to origin/main..." -ForegroundColor Yellow

git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "SUCCESS! All $total commits pushed to GitHub." -ForegroundColor Green
} else {
    Write-Host "Push failed. Try: git push origin main" -ForegroundColor Red
}
