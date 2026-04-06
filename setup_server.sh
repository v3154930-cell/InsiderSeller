#!/bin/bash
set -e

echo "========================================="
echo "🚀 Установка Insider Seller Bot"
echo "========================================="

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}1. Обновление системы...${NC}"
apt update && apt upgrade -y

echo -e "${GREEN}2. Установка Docker и необходимых пакетов...${NC}"
apt install -y docker.io docker-compose curl git
systemctl enable docker
systemctl start docker

echo -e "${GREEN}3. Проверка Docker...${NC}"
docker --version
docker-compose --version

echo -e "${GREEN}4. Создание директории проекта...${NC}"
mkdir -p /opt/insider-seller
cd /opt/insider-seller

echo -e "${GREEN}5. Клонирование репозитория...${NC}"
git clone https://github.com/v3154930-cell/InsiderSeller.git .

echo -e "${GREEN}6. Подготовка файлов для Docker...${NC}"

# Используем feedparser для Python 3.12
cat > requirements.txt << 'EOF'
feedparser==6.0.11
requests==2.31.0
beautifulsoup4==4.12.2
EOF

# Создаём .env файл
cat > .env << 'EOF'
MAX_BOT_TOKEN=ТОКЕН_НЕ_УСТАНОВЛЕН
EOF

# Создаём Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "bot.py"]
EOF

# Создаём docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  bot:
    build: .
    container_name: insider-seller
    restart: always
    env_file:
      - .env
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - bot-network

networks:
  bot-network:
    driver: bridge
EOF

echo -e "${GREEN}7. Сборка и запуск контейнера...${NC}"
docker-compose up -d --build

sleep 10

echo -e "${GREEN}8. Проверка статуса...${NC}"
docker ps -a
echo ""
echo "Логи:"
docker logs insider-seller || true

echo ""
echo "========================================="
echo -e "${GREEN}✅ ГОТОВО!${NC}"
echo "========================================="
echo ""
echo "Теперь нужно:"
echo "1. Отредактировать /opt/insider-seller/.env и вставить токен MAX бота"
echo "2. Перезапустить: cd /opt/insider-seller && docker-compose restart"
echo "3. Смотреть логи: docker logs -f insider-seller"
echo ""
echo "Health check: http://72.56.252.14:8000/health"