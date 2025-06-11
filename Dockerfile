# 1. Windows-Base-Image mit Python 3.10 (nativ für Windows-Container)
FROM mcr.microsoft.com/windows/servercore:ltsc2022

# 2. Installiere Python manuell (da das Base-Image kein Python enthält)
SHELL ["powershell", "-Command"]

# Lade und installiere Python 3.10 (offizielle Installer)
RUN Invoke-WebRequest -Uri https://www.python.org/ftp/python/3.10.9/python-3.10.9-amd64.exe -OutFile python.exe ; `
    Start-Process python.exe -ArgumentList '/quiet InstallAllUsers=1 PrependPath=1' -NoNewWindow -Wait ; `
    Remove-Item -Force python.exe

# 3. Aktualisiere pip
RUN python -m pip install --upgrade pip

# 4. Setze das Arbeitsverzeichnis
WORKDIR C:\app

# 5. Kopiere requirements.txt und installiere Abhängigkeiten
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Kopiere den restlichen Code
COPY . .

# 7. Standardbefehl: Starte dps.py
CMD ["python", "dps.py"]



