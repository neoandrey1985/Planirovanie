#!/usr/bin/env bash
# Планирование спринтов — helper для Linux/macOS/git-bash. Пример: ./scripts/dev.sh up
set -e
cd "$(dirname "$0")/.."

case "${1:-up}" in
  up)    docker compose up --build ;;
  up-d)  docker compose up -d --build ;;
  down)  docker compose down ;;
  clean) docker compose down -v ;;
  logs)  docker compose logs -f ;;
  ps)    docker compose ps ;;
  build) docker compose build ;;
  test)  ( cd backend-java && mvn -B -ntp test ) && python analytics-python/tests/test_compute.py ;;
  seed)  python scripts/gen_initsql.py ;;
  *)     echo "Usage: $0 [up|up-d|down|clean|logs|ps|build|test|seed]" ;;
esac
