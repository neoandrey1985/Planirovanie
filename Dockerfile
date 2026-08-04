# Многопользовательский режим: сервер + общая БД (SQLite через node:sqlite, без внешних зависимостей).
FROM node:22-slim
WORKDIR /app
COPY server ./server
COPY index.html ./index.html
COPY data ./data
# Данные общей БД хранятся здесь. Смонтируйте том на этот путь для сохранности между перезапусками.
ENV PORT=3000 DB_PATH=/app/server/data.db
EXPOSE 3000
CMD ["node", "server/server.js"]
