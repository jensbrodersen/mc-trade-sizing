# 1. Base Python image
FROM python:3.10-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy requirements.txt first (enables Docker layer caching for faster rebuilds)
COPY requirements.txt .

# 4. Install dependencies only if requirements.txt exists and is not empty
RUN if [ -s requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# 5. Copy the rest of the application code
COPY . /app

# 6. Set the default command to run the main script
CMD ["python", "dps.py"]


