Write-Host ""
Write-Host "Loading azd .env file from current environment"
Write-Host ""

foreach ($line in (& azd env get-values)) {
    if ($line -match "([^=]+)=(.*)") {
        $key = $matches[1]
        $value = $matches[2] -replace '^"|"$'
        Set-Item -Path "env:\$key" -Value $value
    }
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to load environment variables from azd environment"
    exit $LASTEXITCODE
}

function func_backend {
    Push-Location ..
    Write-Host 'Creating python virtual environment ".venv"'
    python3 -m venv .venv
    pip install -r app/backend/requirements.txt

    Write-Host "`nRestoring backend python packages`n"

    Push-Location ./app/backend

    Write-Host "`nStarting backend`n"

    $port = 50505
    $localhost = "0.0.0.0"
    & ../.venv/Scripts/python -m quart --app main:app run --port $port --host $localhost --reload --certfile ../cert.pem --keyfile ../key.pem
    if ($LastExitCode -ne 0) {
        Write-Host "Failed to start backend"
        exit $LastExitCode
    }
    Pop-Location
    Pop-Location
}

# TODO: Auto create SSL cert - Lyndon

function func_frontend {
    Write-Host "`nRestoring frontend npm packages`n"

    Push-Location ./frontend
    npm install
    if ($LastExitCode -ne 0) {
        Write-Host "Failed to restore frontend npm packages"
        exit $LastExitCode
    }

    Write-Host "`nBuilding frontend`n"

    npm run build
    if ($LastExitCode -ne 0) {
        Write-Host "Failed to build frontend"
        exit $LastExitCode
    }
    Pop-Location
}

func_frontend
func_backend
