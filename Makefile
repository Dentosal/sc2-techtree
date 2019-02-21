SHELL = /bin/bash

export python := pipenv run -- python

.PHONY: default
default:
	@echo "See Makefile and README.md for instructions"

.PHONY: format
format:
	@$(python) -m black generate
	@cargo fmt

.PHONY: format-check
format-check:
	@$(python) -m black --check generate
	@cargo fmt -- --check

.PHONY: update
update:
	@mkdir -p data
	@ jq -s add -cM generated/results/*.json > data/data.json
	@mkdir -p docs
	@cp generated/visuals/techtree_protoss.png docs/images/
	@cp generated/visuals/techtree_terran.png docs/images/
	@cp generated/visuals/techtree_zerg.png docs/images/
	@dot -Tpng docs/SchemaPlan.dot -o docs/images/SchemaPlan.png

.PHONY: run
run: collect patch validate graph visulize

.PHONY: collect
collect:
	@$(python) -m generate.collect

.PHONY: patch
patch:
	@$(python) -m generate.patch

.PHONY: validate
validate:
	@cargo run --bin validate <(jq -s add -cM generated/results/*.json)

.PHONY: graph
graph:
	@$(python) -m generate.graph

.PHONY: visualize
visualize:
	@$(python) -m generate.visualize

.PHONY: test
test: validate
	@cargo test
