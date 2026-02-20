# tmht — Tell Me How To

AI-powered terminal assistant that generates commands from natural language.

```
$ tmht git create and switch to a new branch called testing

  git checkout -b testing
```

## Installation

Requires Python 3.10+.

```bash
git clone https://github.com/spi/tmht.git
cd tmht
uv sync
```

## Setup

Set an API key for your chosen provider:

```bash
# Gemini (default)
export GEMINI_API_KEY="..."

# Or use any litellm-supported provider
export ANTHROPIC_API_KEY="..."
export OPENAI_API_KEY="..."
```

## Usage

```
tmht <command> <what you want to do>
```

### Examples

```bash
tmht git "create and switch to a new branch called testing"
tmht sed "replace all instances of 'foo' with 'bar' in myfile.txt"
tmht curl "http://example.com and display all request headers"
```

### Arguments

| Argument | Description |
|---|---|
| `command` | The terminal command to get help with (e.g., `git`, `sed`, `curl`) |
| `query` | What you want to do, in natural language |

### Options

| Flag | Description |
|---|---|
| `-h, --help` | Show help message |
| `-V, --version` | Show version |
| `-d, --debug` | Enable debug logging |

## Configuration

| Environment Variable | Description | Default |
|---|---|---|
| `TMHT_MODEL` | LLM model to use ([litellm format](https://docs.litellm.ai/docs/providers)) | `gemini/gemini-3-flash-preview` |
| `GEMINI_API_KEY` | Gemini API key | — |
| `ANTHROPIC_API_KEY` | Anthropic API key | — |
| `OPENAI_API_KEY` | OpenAI API key | — |

### Switching providers

```bash
export TMHT_MODEL="anthropic/claude-haiku-4-5-20251001"
export TMHT_MODEL="openai/gpt-4o-mini"
export TMHT_MODEL="ollama/llama3"
```
