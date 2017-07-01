# Translators



## Commands

### extract

Create or update the template (`.pot`) with `_('...')` strings marked for translation

```bash
python setup.py extract
```

### init_catalog

Create a new language file (`.po`) from template (`.pot`)

```bash
python setup.py init -l es
```

### update

Update an existing language file (`.po`) from template (`.pot`)

```bash
python setup.py update_catalog -l es
```

### compile

Compile language file (`.po`) into a translation file (`.mo`)

```bash
python setup.py compile_catalog -l es
```