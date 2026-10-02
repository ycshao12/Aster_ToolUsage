.PHONY: test demo

test:
	PYTHONPATH=src python -m unittest discover -s tests -v

demo:
	PYTHONPATH=src python examples/minimal_loop.py
