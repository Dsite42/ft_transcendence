FROM python:3.12-alpine

# Install dependencies
RUN apk add --no-cache gcc musl-dev

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create a directory for the app
WORKDIR /app

# Copy the requirements.txt first, to leverage Docker cache
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the container
COPY . /app/

# Expose the ports the app runs on
#EXPOSE 8000
EXPOSE 8765

# Set the command to run the application
CMD ["python", "-m", "matchmaker.matchmaker_service"]
