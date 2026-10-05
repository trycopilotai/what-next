.DEFAULT_GOAL := check

check:
	@python3 -m unittest discover -s tests

.PHONY: check
