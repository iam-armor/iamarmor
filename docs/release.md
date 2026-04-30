# Release Process

iamarmor uses [PyPI Trusted Publishing (OIDC)](https://docs.pypi.org/trusted-publishers/)
for automated, keyless releases. No long-lived API tokens are stored.

## One-time PyPI setup

Before the first release you (or the project maintainer) must register iamarmor
as a **trusted publisher** on PyPI:

1. Log in to [pypi.org](https://pypi.org) and navigate to the project page for
   `iamarmor` (create the project first if it doesn't exist yet by uploading a
   manual build).
2. Go to **Managing → Publishing** and add a new **trusted publisher** with:
   - **Owner**: `iam-armor`
   - **Repository**: `iamarmor`
   - **Workflow filename**: `publish.yml`
   - **Environment name**: `pypi`
3. In the GitHub repository settings, create an **Environment** named `pypi`
   (no required reviewers needed for v1).

## Release steps

1. **Bump version** in `pyproject.toml` and `src/iamarmor/__init__.py`.
2. **Update `CHANGELOG.md`** — add a `## [X.Y.Z] — YYYY-MM-DD` section with
   an `### Added` / `### Fixed` / `### Changed` breakdown.
3. **Commit** the version bump and changelog update to `main`.
4. **Tag** the commit and push:
   ```bash
   git tag v0.1.1
   git push origin v0.1.1
   ```
5. The `publish.yml` GitHub Actions workflow runs automatically:
   - Builds the wheel and sdist via `python -m build`.
   - Publishes to PyPI via OIDC — no secrets required.
6. **Verify** the release:
   ```bash
   pipx install iamarmor==0.1.1
   iamarmor --version
   ```

## Hotfix releases

Follow the same steps with a patch version bump (e.g. `0.1.1`). Never
re-tag an existing version — PyPI will reject the upload.
