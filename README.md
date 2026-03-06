# otas-python-sdk

> Python middleware for capturing all API traffic and forwarding it to the OTAS platform.

---

## Installation

```bash
pip install otas          # once published to PyPI
# or locally:
pip install -e .
```

---

## Quick Start

### 1. Set your SDK key as an environment variable

```bash
export OTAS_SDK_KEY="otas_PocKPi56xDI_..."
export OTAS_SENSITIVE_HEADERS="Authorization,Cookie,X-Internal-Token"
```

> **Never hard-code your SDK key in source files.** For production, set this through your process manager, container environment (e.g. Docker/Kubernetes secrets), or a dedicated secrets manager (e.g. AWS Secrets Manager, HashiCorp Vault).

### 2. Add the middleware to Django settings

```python
# settings.py
MIDDLEWARE = [
    # ... your existing middleware ...
    "otas.OtasMiddleware",  # add at the end
]
```

### 3. Start your server as normal

```bash
python manage.py runserver
```

On startup, `OtasMiddleware` reads `OTAS_SDK_KEY` from the environment, authenticates against the OTAS backend, and automatically begins capturing every request/response pair.

---

## Authentication

Authentication happens automatically when Django loads the middleware — no extra code needed.

If you want to authenticate manually (e.g. in a management command or shell session):

```python
import os
from otas import OtasClient

client = OtasClient(os.environ["OTAS_SDK_KEY"]).authenticate()

print(client.is_authenticated)       # True
print(client.project_name)           # "Git Bash Project"
print(client.project_id)             # "6118d2b5-34f7-4ba3-a70c-2b09f9051b71"
print(client.project_description)    # "Testing with escaped quotes"
```

A successful authentication response from the OTAS backend looks like:

```json
{
  "Status": 1,
  "status_description": "authenticated",
  "Response": {
    "project": {
      "id": "6118d2b5-34f7-4ba3-a70c-2b09f9051b71",
      "name": "Git Bash Project",
      "description": "Testing with escaped quotes"
    }
  }
}
```

---

## Project Structure

```
otas/
├── otas/
│   ├── __init__.py       # public API: OtasMiddleware, OtasClient
│   ├── auth.py           # low-level HTTP authentication call
│   ├── client.py         # OtasClient – holds authenticated project state
│   ├── middleware.py     # Django middleware (capture + forwarding logic)
│   └── exceptions.py     # OtasError, OtasAuthenticationError, OtasConfigurationError
├── tests/
│   └── test_auth.py      # unit tests with mocked HTTP calls
├── pyproject.toml
└── README.md
```

---

## Configuration Reference

| Environment Variable | Required | Description                                                                          |
| -------------------- | -------- | ------------------------------------------------------------------------------------ |
| `OTAS_SDK_KEY`       | ✅       | Your OTAS SDK key. Set via `export OTAS_SDK_KEY='otas_...'` or your secrets manager. |

---

## Error Handling

| Exception                 | When raised                                           |
| ------------------------- | ----------------------------------------------------- |
| `OtasAuthenticationError` | SDK key is invalid or the OTAS backend is unreachable |
| `OtasConfigurationError`  | `OTAS_SDK_KEY` environment variable is not set        |

If `OTAS_SDK_KEY` is missing at startup, the server will raise an `OtasConfigurationError` with instructions:

```
OtasConfigurationError: OTAS_SDK_KEY environment variable is not set.
Export it before starting the server:
  export OTAS_SDK_KEY='otas_...'
```

## Local Testing

1. Install the SDK locally: pip install -e .
2. Go to the test/testsdk folder. This contains a dummy django project to test things with
3. Run

> export OTAS_SDK_KEY='<your-sdk-key>'
> python manage.py runserver

4. Test your new features

## Improvements

1. Batch API call for multiple events at once instead of each event having an API call
2. Having this Batch API call happen in another thread so as to not interrupt the regular flow of the web server
