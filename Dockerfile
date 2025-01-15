# Use Python 3.10 as the base image
FROM python:3.10.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the current directory contents into the container
COPY . .

# Install any dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Specify the command to run your script
CMD ["python", "main.py"]
