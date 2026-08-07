#!/bin/bash
# Автоматический скрипт деплоя на Render.com

set -e

echo "🚀 Автоматический деплой на Render.com"
echo "======================================"
echo ""

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Проверка что мы в правильной директории
if [ ! -f "render.yaml" ]; then
    echo -e "${RED}❌ Ошибка: render.yaml не найден${NC}"
    echo "Убедитесь что вы в корне проекта MySyte"
    exit 1
fi

echo -e "${GREEN}✅ Найден render.yaml${NC}"
echo ""

# Шаг 1: Проверка git
echo "📦 Шаг 1: Проверка Git"
echo "----------------------"

if ! git status &> /dev/null; then
    echo -e "${RED}❌ Git не инициализирован${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Git репозиторий готов${NC}"
echo ""

# Шаг 2: Создание GitHub репозитория
echo "🌐 Шаг 2: GitHub"
echo "----------------"
echo ""
echo "Вам нужно создать репозиторий на GitHub:"
echo "1. Откройте: https://github.com/new"
echo "2. Название: MySyte (или другое)"
echo "3. Private или Public (на выбор)"
echo "4. НЕ добавляйте README, .gitignore, license"
echo "5. Нажмите 'Create repository'"
echo ""
read -p "Нажмите Enter когда создадите репозиторий..."
echo ""

# Запрос GitHub username и repo name
read -p "Введите ваш GitHub username: " github_username
read -p "Введите название репозитория (по умолчанию MySyte): " repo_name
repo_name=${repo_name:-MySyte}

echo ""
echo -e "${YELLOW}⚠️  Для push вам понадобится Personal Access Token${NC}"
echo "Создайте его: https://github.com/settings/tokens"
echo "Scope: repo (полный доступ)"
echo ""
read -p "Нажмите Enter когда будете готовы к push..."

# Добавление remote
echo ""
echo "📤 Добавление remote и push..."

if git remote get-url origin &> /dev/null; then
    echo "Remote 'origin' уже существует, удаляю..."
    git remote remove origin
fi

git remote add origin "https://github.com/${github_username}/${repo_name}.git"
git branch -M main

echo ""
echo "Выполняю push..."
if git push -u origin main; then
    echo -e "${GREEN}✅ Код успешно загружен на GitHub!${NC}"
else
    echo -e "${RED}❌ Ошибка при push${NC}"
    echo "Попробуйте вручную:"
    echo "git push -u origin main"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 GitHub репозиторий создан!${NC}"
echo "URL: https://github.com/${github_username}/${repo_name}"
echo ""

# Шаг 3: Render.com инструкции
echo "☁️  Шаг 3: Деплой на Render.com"
echo "================================"
echo ""
echo "Теперь настройте Render.com:"
echo ""
echo "1. Откройте: https://render.com"
echo "2. Зарегистрируйтесь через GitHub"
echo "3. Нажмите 'New +' → 'Web Service'"
echo "4. Подключите репозиторий: ${repo_name}"
echo "5. Настройки будут взяты из render.yaml автоматически"
echo "6. Добавьте Environment Variables:"
echo "   - TELEGRAM_BOT_TOKEN: (скопируйте из вашего .env файла)"
echo "   - SECRET_KEY: (нажмите Generate)"
echo "   - GEMINI_API_KEY: (скопируйте из .env, если используете)"
echo "7. Нажмите 'Create Web Service'"
echo ""
echo "Деплой займет 3-5 минут."
echo ""
read -p "Нажмите Enter когда деплой завершится..."

# Шаг 4: URL приложения
echo ""
read -p "Введите URL вашего приложения на Render (например: mysyte-web.onrender.com): " render_url

echo ""
echo "🤖 Шаг 4: Настройка Telegram бота"
echo "=================================="
echo ""
echo "Откройте Telegram и найдите @BotFather"
echo "Выполните команды:"
echo ""
echo "  /setdomain"
echo "  @ZEVS_Parsing_orders_bot"
echo "  ${render_url}"
echo ""
read -p "Нажмите Enter когда настроите бота..."

# Шаг 5: Создание админа
echo ""
echo "👤 Шаг 5: Создание администратора"
echo "=================================="
echo ""
echo "В Render Dashboard:"
echo "1. Откройте ваш сервис"
echo "2. Нажмите 'Shell' (справа вверху)"
echo "3. Выполните: python create_admin.py"
echo "4. Введите Telegram ID: 242165070"
echo ""
read -p "Нажмите Enter когда создадите администратора..."

# Финал
echo ""
echo "🎉🎉🎉 ДЕПЛОЙ ЗАВЕРШЕН! 🎉🎉🎉"
echo "=============================="
echo ""
echo -e "${GREEN}✅ Приложение доступно по адресу:${NC}"
echo "   https://${render_url}"
echo ""
echo -e "${GREEN}✅ Страница логина:${NC}"
echo "   https://${render_url}/login"
echo ""
echo -e "${GREEN}✅ Админ-панель:${NC}"
echo "   https://${render_url}/admin"
echo ""
echo "📱 Поделитесь с сотрудниками:"
echo "   https://${render_url}/login"
echo ""
echo "📖 Документация:"
echo "   - DEPLOY_TO_RENDER.md - полная инструкция"
echo "   - README_DEPLOYMENT.md - детальный гайд"
echo ""
echo -e "${YELLOW}⚠️  Free Plan: приложение засыпает после 15 мин неактивности${NC}"
echo "   Первый запрос может занять 30-60 сек"
echo ""
echo "🚀 Готово! Приложение работает в продакшене!"
