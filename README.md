# rcat-radio-network

## Manual signed source candidate (not a station deployment)

At the owner-approved HDA-06 gate, the existing `main` commit can be packaged by the **manual-only** GitHub Actions workflow `.github/workflows/signed-source-release.yml`. Only the `yiwssx` account on `main` can sign and upload a candidate; untrusted pull requests, branch pushes, scheduled runs and public Radio exposure cannot invoke it.

The archive contains only Git-tracked repository source and an exact commit SHA filename. GitHub's Sigstore-backed `actions/attest@v4` signs the **archive's actual bytes**; the Actions artifact expires after 14 days. Download both the archive and checksum file, verify SHA-256 and then independently run `gh attestation verify <archive> --repo yiwssx/rcat-radio-network` to validate the expected owner/repository, trusted workflow identity and source commit. Preserve signed evidence privately if approved.

**Strict boundary:** This source candidate does **not** sign, pin or certify upstream LibreTime/Icecast/PostgreSQL/RabbitMQ container image bytes, operator-generated `/etc/rcat-radio-network` settings, actual RCAT IOT runtime, media licensing, Backup/Restore, public listener security or Production. No `gh release` publication, GHCR push, SSH, DNS, Agent or auto-deployment is performed. The vendor-image digest set and actual Host acceptance remain gated separately in [control HDA-06 #15](https://github.com/yiwssx/rcat-deployment-control/issues/15) and existing [RRN-05](https://github.com/yiwssx/rcat-radio-network/issues/7) / [RRN-06](https://github.com/yiwssx/rcat-radio-network/issues/8).
