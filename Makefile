INN ?= 7707410283

.PHONY: up down logs bench stats reset test clean

up:            ## поднять стенд (первый запуск — несколько минут на сборку)
	docker compose up --build -d
	@echo "\nweb      http://localhost:3000"
	@echo "api      http://localhost:8000/docs"
	@echo "llm-mock http://localhost:8090/admin/stats"
	@echo "\nкарточка http://localhost:3000/company/$(INN)"

down:
	docker compose down -v

logs:
	docker compose logs -f api web llm-mock

bench:         ## измерить: холодное открытие, повторное, деградация провайдера
	python3 bench/bench.py --inn $(INN)

stats:         ## текущие счётчики
	@echo "--- llm-mock ---"
	@curl -s http://localhost:8090/admin/stats | python3 -m json.tool
	@echo "--- api ---"
	@curl -s http://localhost:8000/debug/stats | python3 -m json.tool

reset:         ## обнулить счётчики и забыть сгенерированное описание (INN=...)
	@curl -s -X POST http://localhost:8090/admin/reset > /dev/null
	@curl -s -X POST http://localhost:8000/debug/reset > /dev/null
	@curl -s -X POST http://localhost:8000/debug/purge/$(INN) > /dev/null
	@docker compose exec -T redis redis-cli FLUSHALL > /dev/null
	@echo "счётчики обнулены, описание $(INN) забыто (Redis + БД)"

test:
	docker compose exec -T api pytest -q

clean: down
	docker compose rm -f
