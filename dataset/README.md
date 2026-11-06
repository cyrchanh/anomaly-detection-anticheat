# dataset/

**No data files live here.** This folder holds only `manifest.yaml` files, one per trust level:

| Trust level | Meaning | May be used for |
|---|---|---|
| `real-consented` | Captured from enrolled adult participants under the signed-off policy | train-normal, calibrate, eval-legit, eval-cheat |
| `public-reference` | Third-party datasets with a verified licence | calibrate, eval-cheat |
| `synthetic-calibrated` | Generator output fitted to real/reference statistics | train-normal (with a written mixing reason), stress-test |
| `synthetic-adversarial` | Hard negatives / GAN-style aimbots | eval-cheat, stress-test — **never** train-normal |

Combining datasets across levels is only possible through `fmac.provenance.mix()`. It
requires a purpose and a written reason, and returns a `MixingRecord` that every
derived model or report must carry.

Raw files live under `$FMAC_DATA_ROOT/<trust-level>/<local_path>`. That location must
be **outside** any cloud-sync folder: this repo itself sits on a OneDrive-synced
Desktop.
