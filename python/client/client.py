#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import time
from typing import AsyncIterator

import grpc

from python.api import service_pb2_grpc as svc_grpc
from python.api import message_pb2 as msg


async def do_unary(stub: svc_grpc.JobOrchestrationServiceStub):
    spec = msg.JobSpec(name="demo", queue="default", nodes=1, cpus_per_node=2, executable="/bin/echo", args=["hello"])
    job_id = await stub.SubmitJob(spec)
    print("SubmitJob ->", job_id.id)


async def do_server_streaming(stub: svc_grpc.JobOrchestrationServiceStub, job_id: str):
    print("StreamJobEvents:")
    async for ev in stub.StreamJobEvents(msg.JobId(id=job_id)):
        event_type_name = msg.JobEventType.Name(ev.type)
        print("  ", event_type_name, ev.detail)


async def generate_metrics(job_id: str) -> AsyncIterator[msg.JobMetrics]:
    t0 = int(time.time())
    for i in range(5):
        await asyncio.sleep(0.2)
        yield msg.JobMetrics(id=job_id, cpu_usage_percent=30 + i * 5, memory_usage_mb=512 + i * 16, timestamp_unix=t0 + i)


async def do_client_streaming(stub: svc_grpc.JobOrchestrationServiceStub, job_id: str):
    summary = await stub.UploadJobMetrics(generate_metrics(job_id))
    print("UploadJobMetrics -> avg_cpu=%.1f avg_mem=%.1f" % (summary.avg_cpu_usage_percent, summary.avg_memory_usage_mb))


async def do_bidi(stub: svc_grpc.JobOrchestrationServiceStub, job_id: str):
    async def gen() -> AsyncIterator[msg.Command]:
        for cmd in [
            msg.Command(id=job_id, action=msg.COMMAND_ACTION_PAUSE),
            msg.Command(id=job_id, action=msg.COMMAND_ACTION_RESUME),
            msg.Command(id=job_id, action=msg.COMMAND_ACTION_SCALE, scale_cpus=8),
        ]:
            await asyncio.sleep(0.2)
            yield cmd

    print("JobControl:")
    async for status in stub.JobControl(gen()):
        state_name = msg.JobState.Name(status.state)
        print("  status:", state_name, status.message)


async def main():
    async with grpc.aio.insecure_channel("127.0.0.1:50051") as channel:
        stub = svc_grpc.JobOrchestrationServiceStub(channel)
        # Unary
        response = await stub.SubmitJob(msg.JobSpec(name="demo", queue="q", nodes=1, cpus_per_node=2, executable="/bin/echo"))
        job_id = response.id
        print("Unary SubmitJob ->", job_id)

        # Server streaming
        await do_server_streaming(stub, job_id)

        # Client streaming
        await do_client_streaming(stub, job_id)

        # Bidirectional streaming
        await do_bidi(stub, job_id)


if __name__ == "__main__":
    asyncio.run(main())
