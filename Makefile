.PHONY: install test ui compare docker
install:
	python -m pip install -e ".[dev]"
test:
	pytest -q
ui:
	semanticdiff-ui
compare:
	semanticdiff examples/left.yaml examples/right.json --rules examples/rules.yaml --schema examples/schema.json --policy examples/policy.yaml --format json
docker:
	docker compose up --build
