"""
Module containing potential Translation class.

For now a Translation can be any callable that returns a translated string using the information gleaned from
and `AtomSpan`. This keeps a separation between the logic that defines WHAT is an atom from how it is translated.
This could potentially extend to different translations for different weather provider translations and possibly
even a plugin in system for different language implementations and translation selection at runtime.

An example of a translation might be one that uses the context provided by an AtomSpan in the following way..

Given an Atom that matches the pattern `\bPRES(?P<trend>R|F)R\b`..


def pressure_change(span: AtomSpan, string: str) -> str:
    trend = {"R": "rising", "F": "falling"}.get(span.context["trend"])

    return f"Pressure {trend} rapidly"


The TranslationError should be raised for any specific conditions that aren't met. This will propagate to the
handler that called the translation so it can decide if there is a fallback translation, make an error string,
or to simply pluck the match that couldn't be translated from the input string so it doesn't try to get matched again.
"""

from typing import Callable
from .atom import AtomSpan


Translation = Callable[[AtomSpan, str], str]
