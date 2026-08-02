# Datasets and provenance

## Enabled source

The current corpus begins with 21,349 records imported from the official KiCad
symbol library. Each record retains family, exact component name, description,
footprint, difficulty level, and source path.

KiCad library data is CC BY-SA 4.0 with the KiCad libraries exception. The
derived catalogue is distributed with attribution and the applicable notice.

## Disabled sources

Manufacturer datasheets, textbooks, community Q&A, and research benchmarks are
not automatically incorporated. Each source must have a verified license and
provenance policy first. A public webpage or downloadable PDF does not by itself
grant permission to redistribute it as model training data.

TinyStories is retained only as an architectural reference. It is not the
electronics knowledge base.

## Split policy

Train, validation, and test sets are split by complete KiCad family. Related
part numbers therefore stay together, reducing leakage into held-out tests.
