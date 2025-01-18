FROM python:3.12

WORKDIR /app

# Copy the requirements file (if any)
COPY requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt

# Copy the project directory
COPY . .

# Install the local package
RUN pip install -e .

# Expose the port (if the application serves on a specific port)
# EXPOSE 8000

RUN mkdir -p /var/tmp/jobs

# Command to run the application (entrypoint)
ENTRYPOINT [ "python", "scripts/entrypoint.py" ]