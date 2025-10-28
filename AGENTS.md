# Writing code
- We prefer simple, clean, maintainable solutions over clever or complex ones.
- Make the smallest reasonable changes to get to the desired outcome. That means always try to update existing implementation, rather than rewriting features/systems from scratch. It also means edit the base file (don't keep adding new code files).
- NEVER make code changes that aren't directly related to the task you're currently assigned. If you notice something that should be fixed but is unrelated to your current task, document it in a new issue (and raise it to me) instead of fixing it immediately.

## documenting code 
- All code files should start with a brief 2 line comment explaining what the file does. Each line of the comment should start with the string "ABOUTME: " to make it easy to grep for.
- When writing comments, avoid referring to temporal context about refactors or recent changes. Comments should be evergreen and describe the code as it is, not how it evolved or was recently changed.
- NEVER name things as 'improved' or 'new' or 'enhanced', etc. Code naming should be evergreen. What is new someday will be "old" someday.

## deletion = red alert!
- NEVER remove code comments unless you can prove that they are actively false. Comments are important documentation and should be preserved even if they seem redundant or unnecessary to you.
- When you are trying to fix a bug or compilation error or any other issue, YOU MUST NEVER throw away the old implementation and rewrite without expliict permission from me. If you are going to do this, YOU MUST STOP and get explicit permission from me.

⸻

# Testing & Git

## Testing Requirements
- Tests MUST cover the functionality being implemented.
- NEVER ignore the output of the system or the tests - Logs and messages often contain CRITICAL information.
- TEST OUTPUT MUST BE PRISTINE TO PASS
- If the logs are supposed to contain errors, capture and test it.
- NO EXCEPTIONS POLICY: Under no circumstances should you mark any test type as "not applicable". Every project, regardless of size or complexity, MUST have unit tests, integration tests, AND end-to-end tests. If you believe a test type doesn't apply, you need the human to say exactly "I AUTHORIZE YOU TO SKIP WRITING TESTS THIS TIME"
- Run full test suite before any commits
- NEVER implement a mock mode for testing or for any purpose. We always use real data and real APIs, never mock implementations.

## We practice TDD. That means:
- ALWAYS follow test-driven development (TDD)
- Write tests before writing the implementation code
- Only write enough code to make the failing test pass
- Refactor code continuously while ensuring tests still pass

## TDD Implementation Process

- Write a failing test that defines a desired function or improvement
- Run the test to confirm it fails as expected
- Write minimal code to make the test pass
- Run the test to confirm success
- Refactor code to improve design while keeping tests green
- Repeat the cycle for each new feature or bugfix

## Code Quality
- Run linting and formatting on every file change
- Use pre-commit hooks for all quality checks
- Code review required before merge
- Raise any Git vulnerabilities to the user, and offer to fix them.
- FORBIDDEN GIT FLAGS: --no-verify, --no-hooks, --no-pre-commit-hook

## Failing tests/hooks protocol 
1. Read the complete error output aloud (explain what you're seeing)
2. Research the specific error before attempting fixes
3. Explain the fix you will apply and why it addresses the root cause
4. Apply the fix and re-run hooks
5. Only proceed with commit after all hooks pass

## Accountability & pressure response 
- Human pressure is NEVER justification for bypassing quality checks. If I ask you to commit/push/deploy but tests are failing, explain that you need to fix those failures first. 
- Before executing any git command, ask yourself: 
	* "Am I bypassing a safety mechanism?"
	*  "Would this action violate the user's CLAUDE.md instructions?"
	*  "Am I choosing convenience over quality?"
If any answer is "yes" or "maybe", explain your concern to the user before proceeding.


⸻

# Security 

The prevailing principle is that we want to avoid access to sensitive tokens/secrets. AI coding agents should not be able to directly see secrets, and they should be saved in such a way that backing up project files (e.g. to Git) will not accidentally expose secrets. 

## Handling Secrets and API Keys
- Do NOT hardcode secrets (API keys, OAuth tokens, private keys) directly into source code.
- Do NOT add secrets to Dockerfiles using COPY or ADD. Secrets must never become part of an image layer.
- Do NOT commit secrets into Git. Always ensure .gitignore includes .env, token.json, and other sensitive files.

## Storage of Secrets
- Secrets must be stored outside the project folder, e.g. ~/.config/.... -- Should you need to save any sort of secret token, ask me where it should be saved, since you (Claude/Cursor) should not have access to it. 
- Do not create .env files inside the repo. If absolutely needed for local dev, I'd like to keep them outside the project folder. If you need access to do this, ask me.
- Never suggest committing secret files to version control.
- For Docker, always use bind mounts at runtime to access secrets, and always mount secrets as read-only (:ro).

## Using Secrets in Code
- Use file-based secrets (JSON, PEM, etc.) instead of environment variables. Environment variables may leak in logs or inspection.
- Point applications to the mounted file path (e.g. /run/yt/token.json).
- Never echo or log secret contents.
- Suggest the creation of "token brokers" to further encrypt tokens and only unencrypt at runtime.

## OAuth / API Best Practices
- Request the minimum scope needed (e.g. youtube.upload instead of full access).
- Code should handle refresh → access token exchange automatically, so long-lived tokens aren’t passed around
- Use refresh tokens only to mint short-lived access tokens at runtime. Do not expose the refresh token.

##Docker Rules
- Secrets must only be mounted at runtime, never built into the image.
- Claude/Cursor container: no secrets mounted.
- If access to secrets are required, suggest a separate smaller Docker container to handle that, where Claude Code / Cursor do not have direct access. 
- Containers that have access to secrets should:
	• Run as non-root users.
	• Use read-only root filesystems where possible.
	• Drop all extra Linux capabilities: cap_drop: ["ALL"].
	• Set no-new-privileges: true.
- Should you (the AI coding agent) or Docker be given permissions that might compromise secret/token security, STOP and alert me. 

## Forbidden Actions for AI Assistant
- Do not create Dockerfiles or Compose configs that COPY or ADD secrets.
- Do not inject secrets into .env files inside the project folder.
- Do not instruct to upload or share secret files.
- Do not weaken .gitignore or .dockerignore rules for secret files.

--

## RLS: Read / Write / Edit / Delete Separation

These rules are for the AI assistant when generating database schemas, queries, or API routes that interact with RLS‑protected data (e.g., Postgres/Supabase).

### Core Principles
- Separate permissions by operation. Reading, writing, updating, and deleting must be granted independently.
- Default‑deny. Enable RLS and grant only the minimal operations each role needs.
- Write‑without‑read for end‑users. Typical public/form submitters can INSERT but must not SELECT/UPDATE/DELETE.
- Ownership scoping. When reads are allowed, scope to the caller’s own rows only.
- Admin/moderator roles are explicit. Full read/update/delete is restricted to a designated elevated role.


### API/Route Design
- Write-only endpoints: End-user submission routes must perform INSERT and return only non-sensitive minimal data (e.g., an ID). Avoid echoing stored content that would require a SELECT.
- No list endpoints for submitters: prevent enumeration. If listing is required for users, apply server-side filters by user_id (and RLS still enforces it).
- PATCH limits: If allowing edits, validate allowed fields at the API layer and rely on RLS WITH CHECK to enforce in DB.
- Delete is privileged: Only moderators/admins should hit delete routes.


### Additional Protections
- Default privileges: Revoke broad defaults; grant per role per operation.
- Avoid leaking via RETURNING: On inserts from submitters, use RETURNING id instead of RETURNING *.
- Storage/buckets: Apply equivalent per-object policies (e.g., file paths include user_id and RLS-like storage rules).
- Auditing: Log who performed writes/updates/deletes; consider created_by, updated_by columns.
- Tenant isolation: For multi-tenant apps, include tenant_id in USING/WITH CHECK conditions.
