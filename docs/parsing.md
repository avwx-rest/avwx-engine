# Parsing and Translating

A body of a weather report is generally composed of a series of encoded chunks
that can be interpreted as static or dynamic/encoded and/or single or multi-worded 
elements. These elements follow specific patterns defined in technical documents that
provide for relatively easy decoding (provided they don't change). We'll call these
elements of data "Atoms". 

## The Atom Objects

Atoms define an element's pattern in a corpus of text. They are generally created using
regular expressions, but can be extended to define themselves by other means by subclassing
the `BaseAtom`, provided they implement the `to_atom_span(string: str) -> AtomSpan` method. 
The easiest way to create a `RegexAtom` is using the `RegexAtom.from_pattern_string` class
method. 

```python
from avwx.parsing import RegexAtom

aircraft_mishap_atom = RegexAtom.from_pattern_string(r"\bACFT MSHP\b", "Aircraft Mishap")
```

If you're making a more complicated pattern with some encoded data, you can add flags.

```python
# patterns/remarks.py

BEGINNING_ENDING_OF_PRECIP_AND_TS = r"""
\b
(?P<precip>RA|TS)
(?P<first>
  (?P<first_type>[BE])
  (?P<first_time>\d{4}|\d{2})
)
(?P<second>
  (?#
    Do not match unless time ends word
  )
  (?:(?=[BE]\d{1,4}\b)
  (?P<second_type>[BE])
  (?P<second_time>\d{4}|\d{2})?
)
)?
"""

# remarks.py

begin_end_precip_ts_atom = RegexAtom.from_pattern_string(
    BEGINNING_ENDING_OF_PRECIP_AND_TS, re.VERBOSE, name="Begin End Precip Ts"
)
```

Now this Atom can be easily identified in a bigger string using the `BaseAtom` 
interface. 

```python
s = "The pattern for precip times look like this RAB24E53"

print(begin_end_precip_ts_atom.is_in(s)) # True
```

Keeping the element finding logic separate from the handling logic offers a few
beneifts, with the tradeoff of a little more complexity. Since these elements may
have some undocumented patterns that should be easily added later. Let's add the
ability to match snow as a precip type.

```python
# patterns/remarks.py
BEGINNING_ENDING_OF_PRECIP_AND_TS = r"""
\b
(?P<precip>RA|TS|SN)
(?P<first>
  (?P<first_type>[BE])
  (?P<first_time>\d{4}|\d{2})
)
(?P<second>
  (?#
    Do not match unless time ends word
  )
  (?:(?=[BE]\d{1,4}\b)
  (?P<second_type>[BE])
  (?P<second_time>\d{4}|\d{2})?
)
)?
"""
```

That's it. Now the atom can be used to identify snow as precip type. More about
how these values are used in the translation callables section. 

### `avwx.parsing.BaseAtom`

##### Attributes

* `name: str` - the name of the atom, for debugging purposes

#### Abstract Methods
* `to_atom_string(string: str) -> bool` - return an `AtomString` from the string. If no match
should be made from the string, return an `AtomString` with empty values.

#### Methods

* `is_in(string: str) -> bool` -  return `True` if the atom is contained within the string

* `extract_atom_from_string(string: str) -> Tuple[str, str]` - return a tuple containing the 
match and the string with the match extracted. Raise a `ValueError` if the atom is not in the 
provided string. 

* `find_atom_in_string(string: str) -> Optional[str]` -  return the matching text from a string
or None

### `avwx.parsing.RegexAtom`
Subclass of `BaseAtom` that uses Python's builtin regular expressions internally. 

#### Attributes

* `regex` - a compiled `re.Pattern` object



## The Atom Span Object

`AtomSpan` objects are the main product of the atom classes. They define *where* an atom
is located in a larger body of text. In fact, **all subclasses of BaseAtom must implement
the `to_atom_span(string: str) -> AtomSpan` method**. This is the main driver
for the convenience methods of the `BaseAtom` class.


### `avwx.parsing.AtomSpan`
A named tuple representing the presence of an atom within the body of a larger string
along with any decoded information. 

#### Attributes:

* `match` - string: the raw matching text from a larger string

* `start` - int: the location of the first character of the atom within a larger string

* `end` - int: the first character that does not include the atom, matches string slicing 
behavior

* `context` - `Dict[str, str]`: dict containing decoded information from the atom by keyword

#### [ ] todo: add text field info

## The Translation Callables

For now, translation callables are any callable that accepts an `AtomSpan` and an input string and returns a translated string. This means that a class
could be defined for a more extentable translation that implements the `__call__(self, atom: AtomSpan, string: str) -> str` method. 

```python

# avwx/remarks.py

def begin_end_of_precip_trans(span: AtomStpan, string: str) -> str:
  """Rain|Thunderstorm|Snow began|ended at [HH]MM [and ended at [HH]MM]"""
  match = atom.to_atom_span(string).match

  if match:
      data = atom.to_data_dict(match)
  else:
      raise TranslationError(f"no match could be made from {string}")

  precip_options = {"RA": "Rain", "TS": "Thunderstorm": "SN": "Snow"}

  time_options = {"B": "began", "E": "ended"}

  precip = precip_options.get(data["precip"])
  first_time_type = time_options.get(data["first_type"])
  first_time = data.get("first_time")

  first_string = f"{first_time_type} at {first_time}"

  out = f"{precip} {first_string}"

  if data.get("second"):
      second_time_type = time_options.get(data["second_type"])
      second_time = data.get("second_time")

      second_string = f"and {second_time_type} at {second_time}"

      out = f"{out} {second_string}"

  return out
```

If it is determined that a translation can not be made from the input, `TranslationError` should be raised explaining why. 

## The Handler Object

## Putting It All Together Into a Parser Object

## How Are Errors Handled?

## Can Parsers Be Configured at Runtime?

## Adding Multiple Translations to a Single Handler