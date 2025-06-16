# Storage API

This page documents the Storage API, which provides storage and persistence functionality for the Autoresearch system.

## Storage Manager

The `StorageManager` class is the central component for managing storage operations in the system.

::: autoresearch.storage.StorageManager

## DuckDB Storage Backend

The `DuckDBStorageBackend` class provides a storage backend implementation using DuckDB.

::: autoresearch.storage_backends.DuckDBStorageBackend

## Storage Backup

The storage backup functionality provides tools for backing up and restoring storage data.

::: autoresearch.storage_backup

## Vector Search

The vector search functionality enables semantic search capabilities.

::: autoresearch.storage.StorageManager.vector_search

## Storage Setup and Teardown

The storage setup and teardown functions initialize and clean up storage resources.

::: autoresearch.storage.setup
::: autoresearch.storage.teardown

## VSS Extension Loader

The `VSSExtensionLoader` class manages the loading of vector search extensions.

::: autoresearch.extensions.VSSExtensionLoader