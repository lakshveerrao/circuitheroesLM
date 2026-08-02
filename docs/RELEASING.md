# Releasing

1. Complete all model-card evaluation gates.
2. Run the host C/PyTorch golden comparison.
3. Build the deterministic ZIP with `tools/package_release.py`.
4. Verify every SHA-256 entry and test ZIP extraction.
5. Flash and measure the reference Waveshare device fully offline.
6. Tag the Git commit and attach the ZIP to a GitHub release.
7. Publish the model card, dataset provenance, and negative results.

Do not claim “world's first” without a dated novelty search and reproducible
public demonstration. Use “to our knowledge” until independently verified.
