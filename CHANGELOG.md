# Changelog

All notable changes to Sonnet will be documented here.

## [0.1.0] - 2026-02-06

Initial release.

### Added
- Five poetic forms: haiku, limerick, shakespearean, blank verse, free verse
- CMU Pronouncing Dictionary integration for accurate syllable counting
- Heuristic fallback for words not in dictionary
- Phoneme-based rhyme detection (perfect and slant)
- Meter scanning with iambic, trochaic, anapestic, dactylic patterns
- Constraint checker for validating poems against forms
- LLM-based candidate generation with Ollama
- Candidate ranking by weighted constraint satisfaction
- Interactive TUI for line-by-line composition
- Progress save/resume for long compositions
- CLI commands: generate, check, interactive, forms
- Configuration via environment variables and TOML files
- 209 tests with comprehensive coverage
