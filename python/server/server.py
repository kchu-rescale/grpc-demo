#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import time
from typing import AsyncIterator

import grpc

from python.api import service_pb2_grpc as svc_grpc
from python.api import message_pb2 as msg


class JobOrchestrationService(svc_grpc.JobOrchestrationServiceServicer):
    async def SubmitJob(self, request: msg.JobSpec, context: grpc.aio.ServicerContext) -> msg.JobId:
        # Simulate job submission
        job_id = f"job-{int(time.time()*1000)}"
        print(f"[SubmitJob] name={request.name} -> id={job_id}")
        return msg.JobId(id=job_id)

    async def StreamJobEvents(self, request: msg.JobId, context: grpc.aio.ServicerContext) -> AsyncIterator[msg.JobEvent]:
        # Simulate streaming job events
        print(f"[StreamJobEvents] id={request.id}")
        events = [
            (msg.JOB_EVENT_TYPE_STARTED, "Job submitted"),
            (msg.JOB_EVENT_TYPE_STARTED, "Waiting in queue"),
            (msg.JOB_EVENT_TYPE_NODE_ALLOCATED, "Resources allocated"),
            (msg.JOB_EVENT_TYPE_STARTED, "Job started"),
            (msg.JOB_EVENT_TYPE_STARTED, "Finished successfully"),
        ]
        t0 = int(time.time())
        for i, (etype, detail) in enumerate(events):
            await asyncio.sleep(0.5)
            yield msg.JobEvent(id=request.id, type=etype, detail=detail, timestamp_unix=t0 + i)

    async def UploadJobMetrics(self, request_iterator: AsyncIterator[msg.JobMetrics], context: grpc.aio.ServicerContext) -> msg.MetricsSummary:
        # Client streaming: aggregate metrics
        print("[UploadJobMetrics] start")
        count = 0
        sum_cpu = 0.0
        sum_mem = 0.0
        job_id = ""
        async for m in request_iterator:
            job_id = m.id
            count += 1
            sum_cpu += m.cpu_usage_percent
            sum_mem += m.memory_usage_mb
            print(f"  metrics: cpu={m.cpu_usage_percent:.1f} mem={m.memory_usage_mb:.1f}")
        avg_cpu = (sum_cpu / count) if count else 0.0
        avg_mem = (sum_mem / count) if count else 0.0
        print(f"[UploadJobMetrics] done count={count}")
        return msg.MetricsSummary(id=job_id, avg_cpu_usage_percent=avg_cpu, avg_memory_usage_mb=avg_mem)

    async def JobControl(self, request_iterator: AsyncIterator[msg.Command], context: grpc.aio.ServicerContext) -> AsyncIterator[msg.JobStatus]:
        # Bidirectional streaming: respond to commands
        print("[JobControl] start")
        async for cmd in request_iterator:
            print(f"  command: {cmd.action} (id={cmd.id})")
            state = {
                msg.COMMAND_ACTION_PAUSE: msg.JOB_STATE_PENDING,
                msg.COMMAND_ACTION_RESUME: msg.JOB_STATE_RUNNING,
                msg.COMMAND_ACTION_SCALE: msg.JOB_STATE_RUNNING,
            }.get(cmd.action, msg.JOB_STATE_UNSPECIFIED)
            action_name = msg.CommandAction.Name(cmd.action)
            yield msg.JobStatus(id=cmd.id, state=state, message=f"Applied {action_name}", timestamp_unix=int(time.time()))
        print("[JobControl] end")


async def serve(host: str = "127.0.0.1", port: int = 50051):
    server = grpc.aio.server()
    svc_grpc.add_JobOrchestrationServiceServicer_to_server(JobOrchestrationService(), server)
    listen_addr = f"{host}:{port}"
    server.add_insecure_port(listen_addr)
    print(f"Server listening on {listen_addr}")
    await server.start()
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(serve())
