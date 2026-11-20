.PHONY: api dashboard demo-chat nightshift extension extension-build test dev setup-all setup-api setup-frontends agent agent-watch

api:
	cd services/api && . .venv/bin/activate && uvicorn app.main:app --host 127.0.0.1 --port 8765 --reload

dashboard:
	cd apps/dashboard && npm run dev

demo-chat:
	cd apps/demo-chat && npm run dev -- --port 5174

nightshift:
	cd apps/nightshift && npm run dev

extension-build:
	cd apps/extension && npm run build

test:
	cd services/api && . .venv/bin/activate && pytest -q

setup-api:
	cd services/api && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

setup-frontends:
	cd apps/dashboard && npm install
	cd apps/demo-chat && npm install
	cd apps/nightshift && npm install
	cd apps/extension && npm install

setup-all: setup-api setup-frontends

demo-fixtures:
	cd services/api && . .venv/bin/activate && python ../../scripts/generate_multimodal_fixtures.py

prefetch-whisper:
	cd services/api && . .venv/bin/activate && python ../../scripts/prefetch_whisper.py

agent:
	cd services/api && . .venv/bin/activate && python ../agent/airlock_desktop_agent.py

agent-debug:
	cd services/api && . .venv/bin/activate && AIRLOCK_AGENT_DEBUG=1 python ../agent/airlock_desktop_agent.py

agent-watch:
	@echo "Watching $$HOME/Downloads (set AIRLOCK_WATCH_DIR to override)"
	cd services/api && . .venv/bin/activate && \
		AIRLOCK_WATCH_DIR=$${AIRLOCK_WATCH_DIR:-$$HOME/Downloads} python ../agent/airlock_desktop_agent.py