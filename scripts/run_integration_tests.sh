#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/run_integration_tests.sh [options] [-- pytest-args...]

Runs live integration tests for tutr.
Defaults to your saved tutr config when no override args are provided.

Options:
  --model MODEL            Override model via TUTR_INTEGRATION_MODEL
  --api-key KEY            Override API key via TUTR_INTEGRATION_API_KEY
  --wait-seconds SECONDS   Set TUTR_INTEGRATION_WAIT_SECONDS (default: 0)
  --provider-key-env NAME  Read API key from env var NAME and assign to TUTR_INTEGRATION_API_KEY
  -h, --help               Show this help message

Examples:
  scripts/run_integration_tests.sh --model openai/gpt-4o-mini --provider-key-env OPENAI_API_KEY
  scripts/run_integration_tests.sh --model ollama/llama3 --wait-seconds 1.5
  scripts/run_integration_tests.sh -- --maxfail=1 -k pwd
EOF
}

model_arg=""
api_key_arg=""
wait_seconds_arg=""
provider_key_env_arg=""
extra_pytest_args=()

while (($#)); do
  case "$1" in
    --model)
      shift
      [[ $# -gt 0 ]] || { echo "error: --model requires a value" >&2; exit 2; }
      model_arg="$1"
      ;;
    --api-key)
      shift
      [[ $# -gt 0 ]] || { echo "error: --api-key requires a value" >&2; exit 2; }
      api_key_arg="$1"
      ;;
    --wait-seconds)
      shift
      [[ $# -gt 0 ]] || { echo "error: --wait-seconds requires a value" >&2; exit 2; }
      wait_seconds_arg="$1"
      ;;
    --provider-key-env)
      shift
      [[ $# -gt 0 ]] || { echo "error: --provider-key-env requires a value" >&2; exit 2; }
      provider_key_env_arg="$1"
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      extra_pytest_args=("$@")
      break
      ;;
    *)
      extra_pytest_args+=("$1")
      ;;
  esac
  shift
done

if [[ -n "$model_arg" ]]; then
  export TUTR_INTEGRATION_MODEL="$model_arg"
fi
if [[ -n "$api_key_arg" ]]; then
  export TUTR_INTEGRATION_API_KEY="$api_key_arg"
fi
if [[ -n "$wait_seconds_arg" ]]; then
  export TUTR_INTEGRATION_WAIT_SECONDS="$wait_seconds_arg"
fi
if [[ -n "$provider_key_env_arg" ]]; then
  provider_key_value="${!provider_key_env_arg-}"
  if [[ -z "${provider_key_value}" ]]; then
    echo "error: env var '$provider_key_env_arg' is empty or unset" >&2
    exit 2
  fi
  export TUTR_INTEGRATION_API_KEY="$provider_key_value"
fi

export TUTR_RUN_INTEGRATION=1
export TUTR_INTEGRATION_WAIT_SECONDS="${TUTR_INTEGRATION_WAIT_SECONDS:-0}"

model="${TUTR_INTEGRATION_MODEL:-${TUTR_MODEL:-<saved-config>}}"
echo "Running integration tests with model source: $model"
echo "Wait between live calls (seconds): ${TUTR_INTEGRATION_WAIT_SECONDS}"
uv run pytest -q -m integration "${extra_pytest_args[@]}"
