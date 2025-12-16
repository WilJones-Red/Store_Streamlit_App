# Cstore Dashboard - Helper Scripts
# Common commands for development and deployment

# NOTE: Run these commands from PowerShell in the project root directory

# ============================================================================
# LOCAL DEVELOPMENT
# ============================================================================

# Start the app locally
function Start-App {
    Write-Host "🚀 Starting Cstore Dashboard..." -ForegroundColor Green
    docker compose up
}

# Stop the app
function Stop-App {
    Write-Host "🛑 Stopping Cstore Dashboard..." -ForegroundColor Yellow
    docker compose down
}

# Rebuild and restart (after code changes)
function Restart-App {
    Write-Host "🔄 Rebuilding and restarting..." -ForegroundColor Cyan
    docker compose down
    docker compose up --build
}

# View logs
function Show-Logs {
    docker compose logs -f
}

# ============================================================================
# DEPLOYMENT TO GOOGLE CLOUD RUN
# ============================================================================

# Set your project ID here
$PROJECT_ID = "your-project-id"

# Deploy to Cloud Run
function Deploy-ToCloudRun {
    param(
        [string]$ProjectId = $PROJECT_ID
    )
    
    Write-Host "☁️ Deploying to Google Cloud Run..." -ForegroundColor Blue
    
    # Build
    Write-Host "Building container..." -ForegroundColor Cyan
    gcloud builds submit --tag gcr.io/$ProjectId/cstore-dashboard
    
    # Deploy
    Write-Host "Deploying to Cloud Run..." -ForegroundColor Cyan
    gcloud run deploy cstore-dashboard `
        --image gcr.io/$ProjectId/cstore-dashboard `
        --platform managed `
        --region us-central1 `
        --allow-unauthenticated `
        --memory 512Mi
    
    # Get URL
    Write-Host "✅ Deployment complete!" -ForegroundColor Green
    $url = gcloud run services describe cstore-dashboard --region us-central1 --format 'value(status.url)'
    Write-Host "Your app is live at: $url" -ForegroundColor Green
}

# View Cloud Run logs
function Show-CloudLogs {
    gcloud run logs tail cstore-dashboard --region us-central1
}

# ============================================================================
# DATA MANAGEMENT
# ============================================================================

# Convert CSV to Parquet (for better performance)
function Convert-CSVToParquet {
    param(
        [string]$InputFile,
        [string]$OutputFile
    )
    
    Write-Host "Converting $InputFile to Parquet..." -ForegroundColor Cyan
    
    docker run --rm -v ${PWD}/data:/data python:3.11-slim bash -c "
        pip install polars pyarrow > /dev/null 2>&1
        python -c \"
import polars as pl
df = pl.read_csv('/data/$InputFile')
df.write_parquet('/data/$OutputFile')
print(f'Converted {len(df)} rows to Parquet format')
        \"
    "
    
    Write-Host "✅ Conversion complete: data/$OutputFile" -ForegroundColor Green
}

# ============================================================================
# UTILITIES
# ============================================================================

# Check if Docker is running
function Test-Docker {
    try {
        docker ps | Out-Null
        Write-Host "✅ Docker is running" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
        return $false
    }
}

# Check if gcloud is installed
function Test-GCloud {
    try {
        gcloud version | Out-Null
        Write-Host "✅ Google Cloud SDK is installed" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "❌ Google Cloud SDK not found. Install from: https://cloud.google.com/sdk/docs/install" -ForegroundColor Red
        return $false
    }
}

# Setup check
function Test-Setup {
    Write-Host "`n🔍 Checking setup..." -ForegroundColor Cyan
    
    $dockerOk = Test-Docker
    $gcloudOk = Test-GCloud
    
    if (Test-Path "data") {
        Write-Host "✅ Data directory exists" -ForegroundColor Green
    } else {
        Write-Host "❌ Data directory not found" -ForegroundColor Red
    }
    
    if (Test-Path "Dockerfile") {
        Write-Host "✅ Dockerfile found" -ForegroundColor Green
    } else {
        Write-Host "❌ Dockerfile not found" -ForegroundColor Red
    }
    
    if (Test-Path "docker-compose.yaml") {
        Write-Host "✅ docker-compose.yaml found" -ForegroundColor Green
    } else {
        Write-Host "❌ docker-compose.yaml not found" -ForegroundColor Red
    }
    
    Write-Host "`n📋 Summary:" -ForegroundColor Cyan
    if ($dockerOk) {
        Write-Host "  ✅ Ready for local development" -ForegroundColor Green
    }
    if ($gcloudOk) {
        Write-Host "  ✅ Ready for cloud deployment" -ForegroundColor Green
    }
}

# ============================================================================
# USAGE EXAMPLES
# ============================================================================

function Show-Help {
    Write-Host @"

🏪 Cstore Dashboard Helper Commands
====================================

LOCAL DEVELOPMENT:
  Start-App              - Start the dashboard locally
  Stop-App               - Stop the dashboard
  Restart-App            - Rebuild and restart (after code changes)
  Show-Logs              - View application logs

CLOUD DEPLOYMENT:
  Deploy-ToCloudRun      - Deploy to Google Cloud Run
  Show-CloudLogs         - View Cloud Run logs

DATA UTILITIES:
  Convert-CSVToParquet -InputFile "sales.csv" -OutputFile "sales.parquet"

SETUP:
  Test-Setup             - Check if everything is configured correctly
  Test-Docker            - Check if Docker is running
  Test-GCloud            - Check if gcloud is installed

EXAMPLES:
  # Start locally
  PS> Start-App

  # Convert data to Parquet
  PS> Convert-CSVToParquet -InputFile "sales_data.csv" -OutputFile "sales_data.parquet"

  # Deploy to cloud
  PS> Deploy-ToCloudRun -ProjectId "my-project-123"

  # Check setup
  PS> Test-Setup

For more help, see QUICKSTART.md

"@ -ForegroundColor Cyan
}

# Show help on load
Show-Help
