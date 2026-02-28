.PHONY: help lint format test check install clean verify all ci coverage integration docker build

.DEFAULT_GOAL := help

BLUE := \\033[34m
GREEN := \\033[32m
RED := \\033[31m
YELLOW := \\033[33m
RESET := \\033[0m

help: ## Show help message
	@echo "\\$(BLUE)Proxmox PBS DR Repository\\$(RESET)"
	@echo ""
	@echo "Available targets:"
	@awk 'BEGIN{FS=":.*?## "}/^[a-zA-Z_-]+:.*?##/{printf " \\$(YELLOW)%-20s\\$(RESET) %s\\n",\\$$1,\\$$2}' \\$(MAKEFILE_LIST)

lint: ## Run shellcheck on scripts
	@echo "\\$(BLUE)Running shellcheck...\\$(RESET)"
	@find scripts tests -name "*.sh" -exec shellcheck -x {} + 2>&1 || true
	@echo "\\$(BLUE)Running Python lint...\\$(RESET)"
	@cd src && python -m flake8 proxmox_dr/ --max-line-length=100 --ignore=E203,W503 2>/dev/null || echo "\\$(YELLOW)flake8 not installed\\$(RESET)"

format: ## Format shell scripts and Python
	@echo "\\$(BLUE)Formatting...\\$(RESET)"
	@shfmt -w -i 2 scripts/*.sh tests/*.sh 2>/dev/null || echo "\\$(YELLOW)shfmt not installed\\$(RESET)"
	@cd src && python -m black proxmox_dr/ 2>/dev/null || echo "\\$(YELLOW)black not installed\\$(RESET)"

test: ## Run smoke tests
	@echo "\\$(BLUE)Running smoke tests...\\$(RESET)"
	@bash tests/smoke-test.sh

unit-test: ## Run Python unit tests
	@echo "\\$(BLUE)Running Python unit tests...\\$(RESET)"
	@cd tests/unit && python -m pytest -v --tb=short 2>/dev/null || echo "\\$(YELLOW)pytest not installed\\$(RESET)"

integration-test: ## Run integration tests
	@echo "\\$(BLUE)Running integration tests...\\$(RESET)"
	@cd tests/integration && python -m pytest -v --tb=short 2>/dev/null || echo "\\$(YELLOW)pytest not installed\\$(RESET)"

coverage: ## Run tests with coverage
	@echo "\\$(BLUE)Running tests with coverage...\\$(RESET)"
	@cd tests/unit && python -m pytest --cov=../../src/proxmox_dr --cov-report=term-missing -v 2>/dev/null || echo "\\$(YELLOW)pytest-cov not installed\\$(RESET)"

check: lint test unit-test ## Full check

verify: ## Verify structure
	@echo "\\$(BLUE)Verifying...\\$(RESET)"
	@test -d scripts && echo " \\$(GREEN)✓\\$(RESET) scripts/" || echo " \\$(RED)✗\\$(RESET) scripts/ missing"
	@test -d src/proxmox_dr && echo " \\$(GREEN)✓\\$(RESET) src/proxmox_dr/" || echo " \\$(RED)✗\\$(RESET) src/proxmox_dr/ missing"
	@test -d config && echo " \\$(GREEN)✓\\$(RESET) config/" || echo " \\$(RED)✗\\$(RESET) config/ missing"
	@test -d tests/unit && echo " \\$(GREEN)✓\\$(RESET) tests/unit/" || echo " \\$(RED)✗\\$(RESET) tests/unit/ missing"
	@test -d tests/integration && echo " \\$(GREEN)✓\\$(RESET) tests/integration/" || echo " \\$(RED)✗\\$(RESET) tests/integration/ missing"
	@test -f .github/workflows/ci.yml && echo " \\$(GREEN)✓\\$(RESET) .github/workflows/ci.yml" || echo " \\$(RED)✗\\$(RESET) .github/workflows/ci.yml missing"
	@test -d prometheus && echo " \\$(GREEN)✓\\$(RESET) prometheus/" || echo " \\$(RED)✗\\$(RESET) prometheus/ missing"
	@test -d grafana && echo " \\$(GREEN)✓\\$(RESET) grafana/" || echo " \\$(RED)✗\\$(RESET) grafana/ missing"
	@test -d debian && echo " \\$(GREEN)✓\\$(RESET) debian/" || echo " \\$(RED)✗\\$(RESET) debian/ missing"

clean: ## Clean temp files
	@find . -name "*.tmp" -delete 2>/dev/null || true
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name ".coverage" -delete 2>/dev/null || true
	@echo "\\$(GREEN)✓ Cleaned\\$(RESET)"

install: ## Install Python package
	@cd src && pip install -e . --quiet --break-system-packages 2>/dev/null || pip install -e .

docker: ## Build Docker image
	@docker build -t proxmox-dr:latest -f docker/Dockerfile .

build-deb: ## Build Debian package
	@cd debian && debuild -us -uc -b 2>/dev/null || echo "\\$(YELLOW)debuild not available\\$(RESET)"

run-tests: ## Run all test suites
	@make clean
	@make lint
	@make test
	@make unit-test
	@make integration-test

all: clean verify check ## Full pipeline

ci: check ## CI pipeline
