FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /

# Copy the current directory contents into the container at /app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt


EXPOSE 3306

# Run app.py when the container launches
CMD ["python", "app.py"]