PYTHON ?= python3

.PHONY: test demo label evaluate

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests

label:
	PYTHONPATH=src $(PYTHON) -m document_labeling_eval label

evaluate:
	PYTHONPATH=src $(PYTHON) -m document_labeling_eval evaluate

demo: label evaluate
