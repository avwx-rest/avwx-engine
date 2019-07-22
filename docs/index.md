# AVWX

An aviation weather parsing library.

```python
>>> import avwx
>>> jfk_metar = avwx.Metar('KJFK')
>>> jfk_metar.update()
True
>>> jfk_metar.data.flight_rules
'VFR'
```

These docs could use some love, and I am not a writer. You can help by making a pull request on [GitHub](https://github.com/avwx-rest/AVWX-Engine)

## Contents

* [Getting Started](/getting-started)
* [Station](/station)
* [METAR](/metar)
* [TAF](/taf)
* [PIREP](/pirep)
* [Service](/service)
* [Static Values](/static)
* [Data Structures](/structs)
* [Exceptions](/exceptions)
