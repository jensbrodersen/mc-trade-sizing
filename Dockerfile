# 1. Use a Windows base image (compatible with GitHub Actions Windows runner)
FROM mcr.microsoft.com/windows/servercore:ltsc2022

# 2. Set PowerShell as the default shell for RUN instructions
SHELL ["powershell", "-Command"]

# 3. Download and install Python 3.10 silently, then remove installer
RUN Invoke-WebRequest -Uri https://www.python.org/ftp/python/3.10.9/python-3.10.9-amd64.exe -OutFile python-installer.exe ; `
    & .\python-installer.exe /quiet InstallAllUsers=1 PrependPath=1 ; `
    Remove-Item -Force python-installer.exe

# 4. Upgrade pip
RUN python -m pip install --upgrade pip

# 5. Set the working directory inside the container
WORKDIR C:\app

# 6. Copy dependency list and install required packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 7. Copy application source code into the container
COPY . .

# 8. Set the default command to launch your Python application
CMD ["python", "dps.py"]




