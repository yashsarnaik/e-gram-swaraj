FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /

# Copy the current directory contents into the container at /app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8080 available to the world outside this container
EXPOSE 3306

# Run app.py when the container launches
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=3306"]
