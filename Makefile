.PHONY: api dashboard demo-chat nightshift extension test dev

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