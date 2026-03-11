FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Copy requirements first (better layer caching)
COPY requirements.txt run_core_cont.sh ./

RUN pip install --no-cache-dir -r requirements.txt

# Copy everything from local app/ folder into container /app
RUN mkdir -p /app/app
COPY app/ /app/app

EXPOSE 6400

# Start app (adjust if needed)
CMD ["./run_core_cont.sh"]