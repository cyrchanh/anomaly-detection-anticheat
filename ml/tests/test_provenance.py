from __future__ import annotations

import pytest

from fmac.provenance import (
    DatasetRef, ProvenanceError, Purpose, TrustLevel, load_manifests, mix,
)


def _ref(id_, level, usable=True, **entry):
    return DatasetRef(id_, level, "CC-BY-4.0", usable, dict(entry))


def test_repo_manifests_validate():
    refs = load_manifests()
    assert refs["minecraft-mouse-dynamics-uwec"].usable is False
    assert all(r.trust_level is not TrustLevel.REAL_CONSENTED for r in refs.values())


def test_refs_cannot_be_concatenated_implicitly():
    a = _ref("a", TrustLevel.PUBLIC_REFERENCE)
    b = _ref("b", TrustLevel.SYNTHETIC_CALIBRATED)
    with pytest.raises(ProvenanceError):
        a + b


def test_adversarial_never_trains_normal():
    with pytest.raises(ProvenanceError):
        mix([_ref("adv", TrustLevel.SYNTHETIC_ADVERSARIAL)], purpose=Purpose.TRAIN_NORMAL, reason="x")


def test_fp_claims_only_from_real_data():
    with pytest.raises(ProvenanceError):
        mix([_ref("syn", TrustLevel.SYNTHETIC_CALIBRATED)], purpose=Purpose.EVAL_LEGIT, reason="x")


def test_real_data_requires_consent_signoff():
    unsigned = _ref("real", TrustLevel.REAL_CONSENTED, consent_gate={"policy_version": "0.1", "signed_off": False})
    with pytest.raises(ProvenanceError):
        mix([unsigned], purpose=Purpose.TRAIN_NORMAL, reason="x")


def test_unusable_dataset_blocked():
    with pytest.raises(ProvenanceError):
        mix([_ref("nolicence", TrustLevel.PUBLIC_REFERENCE, usable=False)], purpose=Purpose.CALIBRATE, reason="x")


def test_mix_requires_reason_and_records_levels():
    a = _ref("a", TrustLevel.PUBLIC_REFERENCE)
    with pytest.raises(ProvenanceError):
        mix([a], purpose=Purpose.STRESS_TEST, reason="  ")
    rec = mix([a, _ref("b", TrustLevel.SYNTHETIC_ADVERSARIAL)], purpose=Purpose.STRESS_TEST, reason="smoke")
    assert rec.trust_levels == ("public-reference", "synthetic-adversarial")
