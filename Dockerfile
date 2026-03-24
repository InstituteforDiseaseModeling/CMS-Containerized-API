FROM python:3.11

# Install Wine to run Windows executables on Linux
RUN apt-get update && \
    apt-get install -y \
    wine \
    xvfb \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Configure Wine environment
ENV WINEPREFIX=/root/.wine
ENV DISPLAY=:99

# Initialize Wine and install Wine Mono for .NET support
RUN xvfb-run -a wine wineboot --init && \
    wget -O /tmp/wine-mono.msi https://dl.winehq.org/wine/wine-mono/8.1.0/wine-mono-8.1.0-x86.msi && \
    xvfb-run -a wine msiexec /i /tmp/wine-mono.msi /quiet && \
    rm /tmp/wine-mono.msi

# Set the working directory in the container
WORKDIR /code

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy all files from the root directory (build context is root directory)
COPY . .

# Expose the port that the app will run on
EXPOSE 3100

# Run the application using Uvicorn
CMD ["uvicorn", "api_main:app", "--host", "0.0.0.0", "--port", "3100", "--workers", "4"]