# Use a slim version of Python 3.10 as the base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the dependency list into the container
COPY requirements.txt .

# Upgrade pip and install required dependencies without caching
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the entire project directory into the container
COPY . .

# Expose port 5000 for the REST API
EXPOSE 5000

# Define a volume for storing simulation results persistently
VOLUME /app/results

# Default command: Start the REST API server (change to dps.py if only simulation is needed)
CMD ["python", "dps.py"]
