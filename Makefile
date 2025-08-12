.PHONY: proto clean-proto server client

PYTHON := ./.venv/bin/python
# Check if venv is activated
check-venv:
	@if [ "$$VIRTUAL_ENV" = "" ]; then \
		echo "Error: Please activate your Python virtual environment."; \
		exit 1; \
	fi

# Generate Python gRPC stubs into python/api
proto: check-venv
	$(PYTHON) -m python.proto_build

# Remove generated stubs
clean-proto:
	rm -f python/api/*_pb2.py python/api/*_pb2_grpc.py

# Run the gRPC server
server: check-venv proto
	$(PYTHON) -m python.server.server

# Run the demo client
client: check-venv proto
	$(PYTHON) -m python.client.client
