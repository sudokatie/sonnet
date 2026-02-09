# Sonnet

Constraint-based poetry generator. Because apparently writing poetry wasn't hard enough without a computer judging your syllable counts.

## Why This Exists

Poetry isn't just pretty words - it's words in prison. Meter, rhyme, syllable counts. These constraints force creativity. A sonnet isn't just 14 lines; it's a puzzle where meaning must survive structure.

Most AI poetry tools either ignore form entirely (free verse only) or mangle it badly ("love/dove/above" - really?). Sonnet takes formal constraints seriously: real syllable counting, real rhyme detection, real meter scanning.

You provide the theme and voice. Sonnet handles the mechanical tedium of constraint satisfaction.

## Features

- Five poetic forms: haiku, limerick, Shakespearean sonnet, blank verse, free verse
- Accurate syllable counting (CMU Pronouncing Dictionary + heuristics)
- Real rhyme detection (phoneme-based, not just spelling)
- Meter scanning (iambic pentameter that actually scans)
- Interactive line-by-line composition
- Candidate ranking by constraint satisfaction

## Quick Start

```bash
pip install sonnet

# Generate a haiku about autumn
sonnet generate --form haiku --theme "falling leaves"

# Check if your poem is technically correct
sonnet check poem.txt --form shakespearean

# Compose interactively, line by line
sonnet interactive --form shakespearean --theme "the passage of time"

# List available forms
sonnet forms
```

## How It Works

1. You pick a form and theme
2. Sonnet generates candidate lines
3. Each candidate is scored on: syllable accuracy, rhyme correctness, meter match
4. You pick the ones you like (or regenerate)
5. Repeat until poem is complete

It's not "AI writes your poem." It's collaborative composition where the machine handles the mechanical difficulty while you guide meaning.

## Forms

| Form | Lines | Syllables | Rhyme | Meter |
|------|-------|-----------|-------|-------|
| Haiku | 3 | 5-7-5 | None | None |
| Limerick | 5 | 8-8-5-5-8 | AABBA | Anapestic |
| Shakespearean | 14 | 10 | ABABCDCDEFEFGG | Iambic |
| Blank Verse | 14 | 10 | None | Iambic |
| Free Verse | Variable | None | None | None |

## Configuration

```bash
# Use a specific Ollama model
export SONNET_MODEL=llama3

# Point to remote Ollama
export SONNET_API_URL=http://my-server:11434
```

Or create `~/.config/sonnet/config.toml`:

```toml
[generation]
model = "llama3"
temperature = 0.8
max_candidates = 5
```

## Roadmap

### v0.2 (Planned)
- [ ] More poetic forms (villanelle, sestina, pantoum, tanka, ghazal)
- [ ] Rhyme suggestions while composing
- [ ] Vocabulary constraints (limit to source text words)
- [ ] Improved rhyme word determination
- [ ] Line ranking system for candidate selection

See FEATURE-BACKLOG.md in the clawd repo for detailed acceptance criteria.

## Requirements

- Python 3.10+
- Ollama running locally (or remote API)

## License

MIT

## Author

Katie

---

*Constraints don't limit creativity. They channel it.*
