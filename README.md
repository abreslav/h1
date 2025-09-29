[Create a new repo from template](https://github.com/new?template_name=hello-codespeak&template_owner=codespeak-dev)
  - repo name
  - visibility: public (private is OK)


# 🔴 Now continue in the new repo

The following instructions are copied to the new repo

----



# Set up the CodeSpeak Build Process

- [New Secret](../../settings/secrets/actions/new)
  - `ANTHROPIC_API_KEY`
  - https://console.anthropic.com/settings/keys
- [Install CodeSpeak App](https://github.com/apps/codespeak-build)
  - [Check](../../settings/installations)
- [Edit spec](../../edit/main/spec/main.cs.md)
  - refresh or
  - [Commit history for main.cs.md](../../commits/main/spec/main.cs.md)
- Look at the [commit](../../commit/HEAD)


# Run the app

Locally
  - clone/pull locally
    - `git clone ...`
    - `git pull ...`

Remotely with GitHub Codespaces
  - use codespaces

## Prepare and run
- `uv sync`
- `uv run python manage.py migrate`
- `uv run python manage.py runserver`
- open [http://localhost:8000](http://localhost:8000)

# Deploy with render.com
- create an account at render.com
- create Web Service
- plug in public github url
- build command: `run uv sync --frozen && uv cache prune --ci && uv run manage.py migrate`
- start command: `uv run manage.py runserver 0.0.0.0:$PORT`
- env var: `ALLOWED_HOSTS`, value: `*`
- env var `CSRF_TRUSTED_ORIGINS`: `https://*.render.com`
