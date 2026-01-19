#!/usr/bin/env bash
set -euo pipefail

python -m pip install -q check-jsonschema==0.33.0

check-jsonschema --schemafile contracts/schemas/ingest/IngestRequest.v1.json contracts/examples/ingest/IngestRequest.example.json

check-jsonschema --schemafile contracts/schemas/query/QueryRequest.v1.json contracts/examples/query/QueryRequest.example.json
check-jsonschema --schemafile contracts/schemas/query/QueryResponse.v1.json contracts/examples/query/QueryResponse.example.json

check-jsonschema --schemafile contracts/schemas/fusion/FusionRequest.v1.json contracts/examples/fusion/FusionRequest.example.json
check-jsonschema --schemafile contracts/schemas/fusion/FusionResult.v1.json contracts/examples/fusion/FusionResult.example.json

echo "OK: schemas validate examples"
