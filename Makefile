.DEFAULT_GOAL := check

check:
	@python3 tests/test_integrations.py

.PHONY: check
