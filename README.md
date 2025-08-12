# Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

make proto
```
Generated files will be in `python/api/` and imported as `from python.api import message_pb2, service_pb2_grpc`.

# Run
In separate terminals
`make server`
`make client`


1. Unary RPC (SubmitJob):
   - Sends a `JobSpec`, receives a `JobId`.
2. Server streaming (StreamJobEvents):
   - Streams a sequence of `JobEvent` entries for the job.
3. Client streaming (UploadJobMetrics):
   - Sends a stream of `JobMetrics` and receives a `MetricsSummary`.
4. Bidirectional streaming (JobControl):
   - Sends `Command` messages and receives `JobStatus` updates in response.


## Regenerate protos when changed
If you update files under `proto/`, re-run:
```bash
make proto
```

## Make targets
- `make proto` - Generate Python stubs from proto files
- `make server` - Run the gRPC server
- `make client` - Run the demo client  
- `make clean-proto` - Remove generated stub files
