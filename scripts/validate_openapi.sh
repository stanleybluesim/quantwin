#!/usr/bin/env bash
set -euo pipefail

# Lint OpenAPI (and resolve refs)
npx -y @redocly/cli@latest lint contracts/openapi/openapi.yaml

# Bundle to ensure refs can be resolved into a single file
npx -y @redocly/cli@latest bundle contracts/openapi/openapi.yaml --output /tmp/openapi.bundled.yaml
echo "OK: bundled -> /tmp/openapi.bundled.yaml"
