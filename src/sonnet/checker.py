"""
Constraint checker - validate poems against form constraints.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from sonnet.forms import FormDefinition, get_rhyme_groups, get_syllable_target
from sonnet.syllables import count_line_syllables
from sonnet.rhymes import check_rhyme, RhymeType, get_last_word
from sonnet.meter import match_meter, MeterType


@dataclass
class CheckResult:
    """Result of checking a single constraint on a line."""
    line_index: int
    passed: bool
    constraint: str  # "syllables", "rhyme", "meter"
    expected: str
    actual: str
    score: float = 1.0  # 0-1, 1 = perfect


@dataclass
class PoemAnalysis:
    """Full analysis of a poem against form constraints."""
    form: FormDefinition
    lines: List[str]
    syllable_results: List[CheckResult] = field(default_factory=list)
    rhyme_results: List[CheckResult] = field(default_factory=list)
    meter_results: List[CheckResult] = field(default_factory=list)
    
    @property
    def passed(self) -> bool:
        """Check if all constraints passed."""
        all_results = self.syllable_results + self.rhyme_results + self.meter_results
        return all(r.passed for r in all_results)
    
    @property
    def overall_score(self) -> float:
        """Get overall score (0-1) averaging all constraint scores."""
        all_results = self.syllable_results + self.rhyme_results + self.meter_results
        if not all_results:
            return 1.0
        return sum(r.score for r in all_results) / len(all_results)


def check_syllables(lines: List[str], form: FormDefinition) -> List[CheckResult]:
    """
    Check syllable counts for each line against form requirements.
    
    Args:
        lines: List of poem lines
        form: Form definition with syllable constraints
    
    Returns:
        List of CheckResult for each line
    """
    results = []
    
    for i, line in enumerate(lines):
        expected = get_syllable_target(form, i)
        if expected == 0:  # No constraint (e.g., free verse)
            results.append(CheckResult(
                line_index=i,
                passed=True,
                constraint="syllables",
                expected="any",
                actual=str(count_line_syllables(line)),
                score=1.0
            ))
            continue
        
        actual = count_line_syllables(line)
        diff = abs(actual - expected)
        
        # Allow 1 syllable tolerance, score decreases with distance
        passed = diff <= 1
        score = max(0.0, 1.0 - (diff * 0.2))  # Lose 20% per syllable off
        
        results.append(CheckResult(
            line_index=i,
            passed=passed,
            constraint="syllables",
            expected=str(expected),
            actual=str(actual),
            score=score
        ))
    
    return results


def check_rhymes(lines: List[str], form: FormDefinition) -> List[CheckResult]:
    """
    Check rhyme scheme against form requirements.
    
    Args:
        lines: List of poem lines
        form: Form definition with rhyme scheme
    
    Returns:
        List of CheckResult for rhyme pairs
    """
    results = []
    
    if not form.rhyme_scheme:
        return results  # No rhyme constraint
    
    groups = get_rhyme_groups(form.rhyme_scheme)
    
    for letter, indices in groups.items():
        if len(indices) < 2:
            continue  # Need at least 2 lines to check rhyme
        
        # Check each line against the first line in its group
        first_idx = indices[0]
        first_word = get_last_word(lines[first_idx]) if first_idx < len(lines) else ""
        
        for idx in indices[1:]:
            if idx >= len(lines):
                results.append(CheckResult(
                    line_index=idx,
                    passed=False,
                    constraint="rhyme",
                    expected=f"{letter} (missing line)",
                    actual="",
                    score=0.0
                ))
                continue
            
            current_word = get_last_word(lines[idx])
            rhyme_type = check_rhyme(first_word, current_word)
            
            if rhyme_type == RhymeType.PERFECT:
                passed = True
                score = 1.0
            elif rhyme_type == RhymeType.SLANT:
                passed = True  # Accept slant rhymes
                score = 0.7
            else:
                passed = False
                score = 0.0
            
            results.append(CheckResult(
                line_index=idx,
                passed=passed,
                constraint="rhyme",
                expected=f"{letter} rhymes with line {first_idx + 1} ({first_word})",
                actual=f"{current_word} ({rhyme_type.value})",
                score=score
            ))
    
    return results


def check_meter(lines: List[str], form: FormDefinition) -> List[CheckResult]:
    """
    Check meter pattern against form requirements.
    
    Args:
        lines: List of poem lines
        form: Form definition with meter
    
    Returns:
        List of CheckResult for each line
    """
    results = []
    
    if not form.meter:
        return results  # No meter constraint
    
    # Map form meter string to MeterType
    meter_map = {
        "iambic": MeterType.IAMBIC,
        "trochaic": MeterType.TROCHAIC,
        "anapestic": MeterType.ANAPESTIC,
        "dactylic": MeterType.DACTYLIC,
        "spondaic": MeterType.SPONDAIC,
    }
    
    meter_type = meter_map.get(form.meter.lower())
    if not meter_type:
        return results  # Unknown meter
    
    expected_syllables = form.syllables if isinstance(form.syllables, int) else 10
    
    for i, line in enumerate(lines):
        score = match_meter(line, meter_type, expected_syllables)
        
        # Consider passing if score >= 0.6
        passed = score >= 0.6
        
        results.append(CheckResult(
            line_index=i,
            passed=passed,
            constraint="meter",
            expected=form.meter,
            actual=f"score={score:.2f}",
            score=score
        ))
    
    return results


def check_poem(lines: List[str], form: FormDefinition) -> PoemAnalysis:
    """
    Fully analyze a poem against form constraints.
    
    Args:
        lines: List of poem lines
        form: Form definition to check against
    
    Returns:
        PoemAnalysis with all constraint results
    """
    analysis = PoemAnalysis(
        form=form,
        lines=lines,
        syllable_results=check_syllables(lines, form),
        rhyme_results=check_rhymes(lines, form),
        meter_results=check_meter(lines, form),
    )
    
    return analysis


def format_analysis(analysis: PoemAnalysis) -> str:
    """
    Format analysis results as human-readable string.
    
    Args:
        analysis: PoemAnalysis to format
    
    Returns:
        Formatted string with results
    """
    lines = [
        f"Form: {analysis.form.name}",
        f"Overall: {'PASS' if analysis.passed else 'FAIL'} ({analysis.overall_score:.0%})",
        "",
    ]
    
    if analysis.syllable_results:
        lines.append("Syllables:")
        for r in analysis.syllable_results:
            status = "OK" if r.passed else "FAIL"
            lines.append(f"  Line {r.line_index + 1}: {r.actual}/{r.expected} [{status}]")
        lines.append("")
    
    if analysis.rhyme_results:
        lines.append("Rhymes:")
        for r in analysis.rhyme_results:
            status = "OK" if r.passed else "FAIL"
            lines.append(f"  Line {r.line_index + 1}: {r.actual} [{status}]")
        lines.append("")
    
    if analysis.meter_results:
        lines.append("Meter:")
        for r in analysis.meter_results:
            status = "OK" if r.passed else "FAIL"
            lines.append(f"  Line {r.line_index + 1}: {r.actual} [{status}]")
    
    return "\n".join(lines)
