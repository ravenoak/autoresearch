# Distributed Execution API

This page documents the utilities for running agents in distributed mode using either Ray or standard multiprocessing.

## Executors

::: autoresearch.distributed.RayExecutor

::: autoresearch.distributed.ProcessExecutor

## Brokers

::: autoresearch.distributed.InMemoryBroker
::: autoresearch.distributed.RedisQueue

## Coordination Helpers

::: autoresearch.distributed.StorageCoordinator
::: autoresearch.distributed.ResultAggregator
::: autoresearch.distributed.start_storage_coordinator
::: autoresearch.distributed.start_result_aggregator
::: autoresearch.distributed.publish_claim
