FROM python:3.10-slim

# Cài gói hệ thống bắt buộc để biên dịch mysqlclient
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    libssl-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Tạo thư mục và copy mã nguồn vào container
WORKDIR /app
COPY . .

# Cài requirements
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Expose port Flask
EXPOSE 5000

# Chạy Flask
CMD ["python3", "main.py"]
