"""
Michael duPont - michael@mdupont.com
AVWX-Engine : avwx/summary.py

Contains functions for combining translations into a summary string
"""

from avwx.static import _

def metar(trans: {str: object}) -> str:
    """Condense the translation strings into a single report summary string"""
    summary = []
    if 'Wind' in trans and trans['Wind']:
        summary.append(_('Winds {}'.format(trans['Wind'])))
    if 'Visibility' in trans and trans['Visibility']:
        summary.append(_('Vis {}'.format(trans['Visibility'][:trans['Visibility'].find(' (')].lower())))
    if 'Temperature' in trans and trans['Temperature']:
        summary.append(_('Temp {}'.format(trans['Temperature'][:trans['Temperature'].find(' (')])))
    if 'Dewpoint' in trans and trans['Dewpoint']:
        summary.append(_('Dew {}'.format(trans['Dewpoint'][:trans['Dewpoint'].find(' (')])))
    if 'Altimeter' in trans and trans['Altimeter']:
        summary.append(_('Alt {}'.format(trans['Altimeter'][:trans['Altimeter'].find(' (')])))
    if 'Other' in trans and trans['Other']:
        summary.append(trans['Other'])
    if 'Clouds' in trans and trans['Clouds']:
        summary.append(trans['Clouds'].replace(_(' - Reported AGL'), ''))
    return ', '.join(summary)

def taf(trans: {str: object}) -> str:
    """Condense the translation strings into a single forecast summary string"""
    summary = []
    if 'Wind' in trans and trans['Wind']:
        summary.append(_('Winds {}'.format(trans['Wind'])))
    if 'Visibility' in trans and trans['Visibility']:
        summary.append(_('Vis {}'.format(trans['Visibility'][:trans['Visibility'].find(' (')].lower())))
    if 'Altimeter' in trans and trans['Altimeter']:
        summary.append(_('Alt {}'.format(trans['Altimeter'][:trans['Altimeter'].find(' (')])))
    if 'Other' in trans and trans['Other']:
        summary.append(trans['Other'])
    if 'Clouds' in trans and trans['Clouds']:
        summary.append(trans['Clouds'].replace(_(' - Reported AGL'), ''))
    if 'Wind-Shear' in trans and trans['Wind-Shear']:
        summary.append(trans['Wind-Shear'])
    if 'Turbulance' in trans and trans['Turbulance']:
        summary.append(trans['Turbulance'])
    if 'Icing' in trans and trans['Icing']:
        summary.append(trans['Icing'])
    return ', '.join(summary)
