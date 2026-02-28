.PHONY: help lint format test check install clean verify all ci

.DEFAULT_GOAL := help

BLUE := \\033[34m
GREEN := \\033[32m
RED := \\033[31m
YELLOW := \\033[33m
RESET := \\033[0m

help: ## Show help message
	@echo "\$(BLUE)Proxmox PBS DR Repository\$(RESET)"
	@awk 'BEGIN{FS=":.*?## "}/^[a-zA-Z_-]+:.*?##/{printf " \$(YELLOW)%-12s\$(RESET) %s\\n",\$$1,\$$2}' \$(MAKEFILE_LIST)

lint: ## Run shellcheck on scripts
	@echo "\$(BLUE)Running shellcheck...\$(RESET)"
	@find scripts tests -name "*.sh" -exec shellcheck -x {} + 2>&1

format: ## Format shell scripts
	@echo "\$(BLUE)Formatting...\$(RESET)"
	@shfmt -w -i 2 scripts/*.sh tests/*.sh 2>/dev/null || echo "\$(YELLOW)shfmt not installed\$(RESET)"

test: ## Run smoke tests
	@echo "\$(BLUE)Running tests...\$(RESET)"
	@bash tests/smoke-test.sh

check: lint test ## Full check

verify: ## Verify structure
	@echo "\$(BLUE)Verifying...\$(RESET)"
	@test -d scripts && echo " \$(GREEN)✓\$(RESET) scripts/" || echo " \$(RED)✗\$(RESET) scripts/ missing"
	@test -d cron && echo " \$(GREEN)✓\$(RESET) cron/" || echo " \$(RED)✗\$(RESET) cron/ missing"
	@test -d docs && echo " \$(GREEN)✓\$(RESET) docs/" || echo " \$(RED)✗\$(RESET) docs/ missing"
	@test -d tests && echo " \$(GREEN)✓\$(RESET) tests/" || echo " \$(RED)✗\$(RESET) tests/ missing"

clean: ## Clean temp files
	@find . -name "*.tmp" -delete 2>/dev/null || true
	@echo "\$(GREEN)✓ Cleaned\$(RESET)"

ci: check ## CI pipeline
all: verify check ## Full pipeline
