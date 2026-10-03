# ygo-gym

YGO Gym is a research environment for Yu-Gi-Oh! built on Project Ignis's `ygopro-core`.

The current engine layer loads the pinned card database and scripts, creates seeded 1v1 duels, decodes ocgcore player decisions, and exposes the complete current set of semantic legal actions. Compound selections are represented as atomic action sequences before YGO Gym submits the resulting response to ocgcore.
