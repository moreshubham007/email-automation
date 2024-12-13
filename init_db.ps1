# Clean up existing database and migrations
Write-Host "Cleaning up existing database and migrations..." -ForegroundColor Yellow
Remove-Item -Force -Recurse instance/app.db -ErrorAction SilentlyContinue
Remove-Item -Force -Recurse migrations -ErrorAction SilentlyContinue

# Create instance directory with proper permissions
Write-Host "Creating instance directory..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "instance"

# Set permissions
Write-Host "Setting permissions..." -ForegroundColor Yellow
$acl = Get-Acl "instance"
$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$fileSystemRights = [System.Security.AccessControl.FileSystemRights]::FullControl
$type = [System.Security.AccessControl.AccessControlType]::Allow

$fileSystemAccessRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    $identity, $fileSystemRights, $type
)

$acl.SetAccessRule($fileSystemAccessRule)
Set-Acl "instance" $acl

# Initialize database
Write-Host "Initializing database..." -ForegroundColor Yellow
$env:FLASK_APP = "app"
flask db init
flask db migrate -m "initial migration"
flask db upgrade

Write-Host "Database initialization complete!" -ForegroundColor Green 