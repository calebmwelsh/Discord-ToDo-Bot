# Use Python 3.10 as the base image
FROM python:3.10.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file first (to optimize caching)
COPY requirements.txt /app/

# Install any dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of your application files
COPY . .

# Specify the command to run your script
CMD ["python", "main.py"]
