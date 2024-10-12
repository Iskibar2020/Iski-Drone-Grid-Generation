# Use a base image with Python 3.9
FROM python:3.9

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
    gdal-bin \
    libgdal-dev \
    gcc \
    && apt-get clean

# Set environment variables for GDAL
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install necessary Python packages
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define the command to run the application
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000"]
