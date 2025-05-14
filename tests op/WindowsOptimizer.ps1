# Encoding: UTF-8
$OutputEncoding = [System.Text.Encoding]::UTF8

# Путь к лог-файлу
$LogPath = "$env:TEMP\WindowsOptimizer_Log.txt"

# Функция для записи в лог
function Write-Log {
    param (
        [string]$Message,
        [string]$Level = "INFO"
    )
    
    $LogTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "[$LogTime] [$Level] $Message"
    
    # Выводим в консоль
    if ($Level -eq "ERROR") {
        Write-Host $LogEntry -ForegroundColor Red
    } elseif ($Level -eq "WARNING") {
        Write-Host $LogEntry -ForegroundColor Yellow
    } else {
        Write-Host $LogEntry -ForegroundColor Green
    }
    
    # Записываем в файл лога
    $LogEntry | Out-File -FilePath $LogPath -Append -Encoding UTF8
}

# Функция оптимизации служб Windows
function Optimize-Services {
    param([bool]$Revert = $false)
    
    Write-Host "Оптимизация служб Windows..." -ForegroundColor Cyan
    
    $servicesToDisable = @("DiagTrack", "dmwappushservice", "SysMain", "XboxGipSvc", "XblAuthManager", "XblGameSave", "XboxNetApiSvc")
    
    foreach ($service in $servicesToDisable) {
        $svc = Get-Service -Name $service -ErrorAction SilentlyContinue
        
        if ($svc) {
            $currentState = $svc.StartType
            $backupFile = "${1}:TEMP\service_${1}.bak"
            $currentState | Out-File -FilePath $backupFile -Force
            
            if ($Revert) {
                if (Test-Path $backupFile) {
                    $originalState = Get-Content $backupFile
                    Write-Host "Восстановление службы $service в состояние $originalState..."
                    try {
                        Set-Service -Name $service -StartupType $originalState -ErrorAction SilentlyContinue
                        Write-Host "Служба $service восстановлена." -ForegroundColor Green
                    }
                    catch {
                        Write-Warning "Не удалось восстановить службу ${1}: ${1}"
                    }
                }
            }
            else {
                try {
                    Set-Service -Name $service -StartupType Disabled -ErrorAction SilentlyContinue
                    Write-Host "Служба $service отключена." -ForegroundColor Green
                }
                catch {
                    Write-Warning "Не удалось отключить службу ${1}: ${1}"
                }
            }
        }
        else {
            Write-Host "Служба $service не найдена на данном компьютере." -ForegroundColor Yellow
        }
    }
}

# Функция оптимизации визуальных эффектов
function Optimize-VisualEffects {
    Write-Host "Оптимизация визуальных эффектов..." -ForegroundColor Cyan
    
    try {
        # Отключение эффектов прозрачности
        Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize" -Name "EnableTransparency" -Type DWord -Value 0
        # Отключение эффектов анимации
        Set-ItemProperty -Path "HKCU:\Control Panel\Desktop" -Name "UserPreferencesMask" -Type Binary -Value ([byte[]](0x90,0x12,0x03,0x80,0x10,0x00,0x00,0x00))
        # Отключение эффектов при наведении
        Set-ItemProperty -Path "HKCU:\Control Panel\Desktop" -Name "MenuShowDelay" -Type DWord -Value 0

        Write-Host "Визуальные эффекты оптимизированы." -ForegroundColor Green
    }
    catch {
        Write-Warning "Произошла ошибка при оптимизации визуальных эффектов: $_"
    }
}

# Функция настройки плана электропитания
function Optimize-PowerPlan {
    Write-Host "Настройка плана электропитания..." -ForegroundColor Cyan
    
    try {
        # Установка схемы электропитания "Сбалансированная"
        powercfg -setactive 381b4222-f694-41f0-9685-ff5bb260df2e
        # Отключение гибернации
        powercfg -hibernate off
        # Отключение спящего режима
        powercfg -change -standby-timeout-ac 0
        powercfg -change -standby-timeout-dc 0

        Write-Host "План электропитания оптимизирован." -ForegroundColor Green  
    }
    catch {
        Write-Warning "Произошла ошибка при настройке плана электропитания: $_"
    }
}

# Функция очистки кэша и оптимизации Telegram 
function Optimize-Telegram {
    Write-Host "Оптимизация Telegram..." -ForegroundColor Cyan

    try {
        $mediaCachePath = "${1}:APPDATA\Telegram Desktop\tdata\user_data\media_cache\*"
        $tempFilesPath = "${1}:APPDATA\Telegram Desktop\tdata\user_data\temp\*"

        if (Test-Path $mediaCachePath) {
            Write-Host "Очистка кэша медиафайлов Telegram..."
            Remove-Item -Path $mediaCachePath -Recurse -Force -ErrorAction SilentlyContinue
        }

        if (Test-Path $tempFilesPath) {
            Write-Host "Очистка временных файлов Telegram..."
            Remove-Item -Path $tempFilesPath -Recurse -Force -ErrorAction SilentlyContinue
        }

        Write-Host "Рекомендации по настройкам Telegram для снижения использования ресурсов:"
        Write-Host "- Отключите автозагрузку медиафайлов в настройках"
        Write-Host "- Ограничьте максимальный размер кэша данных (настройка 'Cache max size')"
        Write-Host "- Включите режим экономии трафика"
        Write-Host "- Отключите ненужные уведомления и звуки"

        Write-Host "Telegram оптимизирован." -ForegroundColor Green
    }
    catch {
        Write-Warning "Произошла ошибка при оптимизации Telegram: $_"
    }
}

# Функция меню
function Show-Menu {
    Write-Host "========= Меню оптимизации Windows ========="
    Write-Host "1. Оптимизация служб Windows"
    Write-Host "2. Оптимизация визуальных эффектов"
    Write-Host "3. Настройка плана электропитания"
    Write-Host "4. Оптимизация Telegram"
    Write-Host "5. Выполнить все оптимизации"
    Write-Host "6. Восстановить настройки"
    Write-Host "0. Выход"
    Write-Host "============================================="

    $choice = Read-Host "Выберите действие"

    switch ($choice) {
        1 { Optimize-Services }

# Функция отображения прогресса
function Show-Progress {
    param (
        [string]$Activity,
        [int]$PercentComplete
    )
    
    Write-Progress -Activity $Activity -PercentComplete $PercentComplete
    Write-Host "[$($Activity)]: $PercentComplete%" -ForegroundColor Cyan
}
        2 { Optimize-VisualEffects }
        3 { Optimize-PowerPlan }
        4 { Optimize-Telegram }
        5 { 
            Optimize-Services
            Optimize-VisualEffects
            Optimize-PowerPlan
            Optimize-Telegram
        }
        6 { 
            Optimize-Services -Revert $true
            # Добавить функции восстановления для других оптимизаций
        }
        0 { exit }
        Default { Write-Host "Неверный выбор. Попробуйте еще раз." -ForegroundColor Red }
    }

    Show-Menu
}

# Основной код скрипта
Clear-Host
Write-Host "Проверка прав администратора..."

if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Warning "Для выполнения скрипта требуются права администратора."
    Write-Host "Запустите PowerShell от имени администратора и повторите попытку."
    break
}

Write-Host "Сбор информации о системе..." -ForegroundColor Cyan
$computerInfo = Get-ComputerInfo
$osInfo = Get-CimInstance -ClassName Win32_OperatingSystem
$processorInfo = Get-CimInstance -ClassName Win32_Processor
$gpuInfo = Get-CimInstance -ClassName Win32_VideoController
$ramInfo = Get-CimInstance -ClassName Win32_PhysicalMemory

Write-Host "Информация о системе:"
Write-Host "Операционная система: $($osInfo.Caption) $($osInfo.OSArchitecture)"
Write-Host "Процессор: $($processorInfo.Name)"
Write-Host "Оперативная память: $($ramInfo.Capacity / 1GB) GB"
Write-Host "Видеокарта: $($gpuInfo.Name)"

Show-Menu
