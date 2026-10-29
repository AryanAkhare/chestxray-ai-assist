# Risk management log

Qualitative ISO 14971-style engineering log. Ratings are preliminary design judgments, not quantified clinical risk estimates. Verification status describes this prototype only.

| Hazard | Cause | Harm | Severity | Likelihood | Mitigation | Residual risk | Verification |
|---|---|---|---|---|---|---|---|
| False negative / missed finding | Model score below threshold | Reviewer overlooks a finding | High | Unknown | Persistent disclaimer; exact no-flag message; clinician review required | High | UI inspected; clinical performance not verified |
| False positive | Model score above threshold | Unnecessary follow-up or concern | Moderate | Unknown | Neutral signal wording; score and threshold shown together | Moderate | UI inspection |
| Automation bias | Reviewer over-trusts ranked outputs | Independent review is weakened | High | Unknown | Research-only framing and explicit review status | High | Human factors study absent |
| Heat-map over-reliance | Heat map interpreted as explanation | Misleading localization | Moderate | Unknown | Heat maps are not implemented; required caption reserved for future implementation | Moderate | Not verified |
| Domain shift | Different scanner, pediatric, lateral, or portable image | Unreliable output | High | Unknown | Warn on DICOM lateral/non-CR/DX; disclose NIH frontal-only training | High | DICOM integration tests pending |
| Wrong orientation or MONOCHROME1 handling | Incorrect metadata or inversion | Altered input and output | High | Unknown | MONOCHROME1 inversion; explicit image review | Moderate | DICOM fixture tests pending |
| Wrong patient mix-up | User selects the wrong file/case identifier | Results associated with another case | High | Unknown | Case ID is explicit; no patient tags are displayed or stored | Moderate | Workflow test pending |
| Rare Hernia output misread | Very small positive sample and uncertain quality | Overconfidence in an unstable signal | High | Unknown | Low-reliability rule and caveat on the model card | High | Metrics sourced; clinical validation absent |
| Threshold or ensemble misuse | Threshold modified or models combined incorrectly | Misleading flags | High | Unknown | Phase 1 uses saved model-specific thresholds only; ensemble absent | Moderate | Threshold script pending run |
| PHI leakage | DICOM tags or pixels exposed | Privacy breach | High | Unknown | Pixel bytes not persisted; patient identifiers are not returned or logged | Moderate | Security testing pending |
| Tampered model file | Weights modified after conversion | Untrusted output | High | Low | Runtime verifies SHA-256 against metadata and refuses mismatch | Low | Tamper test pending |
| Stale model version | Old or mismatched weights and result tables | Incorrect thresholds or audit context | Moderate | Unknown | Hash displayed and audited; source results bound by configuration | Moderate | Version lifecycle process not implemented |
| Malicious or oversized upload | Crafted file or decompression resource exhaustion | Service outage or code execution | High | Unknown | Size limit, extension plus signature check, image pixel limit; no unpickling of uploads | Moderate | Fuzz tests pending |
