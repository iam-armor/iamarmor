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

## Release steps (GitHub web UI — no local tagging required)

All release steps are performed entirely on the GitHub website; no local
`git tag` or `git push` commands are needed.

1. **Bump version** in `pyproject.toml` and `src/iamarmor/__init__.py` on a
   release branch, update `CHANGELOG.md`, and merge the PR to `main`.
2. Open the repository on GitHub and click **Releases** in the right sidebar,
   then **Draft a new release**.
3. In the **Choose a tag** field, type the new tag (e.g. `v0.2.0`).
   GitHub will offer to *create the tag on publish* — select **`main`** as the
   target branch.
4. Set the **Release title** to `v0.2.0` and paste the relevant section from
   `CHANGELOG.md` into the description field.
5. Click **Publish release**.
6. GitHub automatically creates the tag on `main` and triggers the
   `publish.yml` workflow. Monitor it under **Actions → publish**.
7. **Verify** the release on PyPI:
   - Visit <https://pypi.org/project/iamarmor/>
   - Or run: `pip install iamarmor==0.2.0 && iamarmor --version`

## Hotfix releases

Follow the same steps with a patch version bump (e.g. `0.2.1`). Never
re-tag an existing version — PyPI will reject the upload.

