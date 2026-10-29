# Model card

## Summary

The prototype exposes the supplied baseline and experiments A/B/C/D. The model configuration files describe ResNet18 with a 14-output linear layer and independent sigmoid scores. The model does not output “No Finding.” Thresholds and evaluation values are loaded from the supplied result CSVs at runtime.

## Data and preprocessing

The supplied configuration describes the official NIH ChestX-ray14 split and grayscale, PIL bilinear resize to 224 × 224, three-channel replication, and ImageNet mean/std normalization. The application does not validate the claims in the training report independently.

## Important interpretation caveats

- D had the best observed macro AP, but paired patient-bootstrap intervals do not support a difference between D and B. D is selected by the reported ranking, not proven superiority.
- The comparison ranked conditions using the test set, so the winning test metrics are mildly optimistic. There is no external validation.
- The Hernia GAN failed the supplied quality check, no synthetic Hernia images were used, and there were 86 test positives. Hernia output is very uncertain.
- Pneumonia did not improve. Fibrosis AP improved while AUROC did not clearly improve.
- One training seed was used per condition; training variability is not captured.
- Synthetic images were generated at 128 px and upsampled. Their disease label validity is not established; only the target label was supervised.
- NIH labels were derived from report NLP and are noisy. The model estimates agreement with those labels, not clinical truth.
- Test prevalence is the natural prevalence in the NIH hospital dataset, not in a screening population.

Per-finding metrics and thresholds appear in the Model Card UI from the matching CSVs. Values are not manually copied into the interface.
