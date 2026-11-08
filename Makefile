.PHONY: setup test run
setup:            ## enable the pre-commit test hook
	git config core.hooksPath .githooks
test:
	python3 -m unittest discover -s tests -t . -q
run:
	python3 -m csodisc --out out
