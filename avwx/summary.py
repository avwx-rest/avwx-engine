"""
Michael duPont - michael@mdupont.com
AVWX-Engine : avwx/summary.py

Contains functions for combining translations into a summary string
"""


def metar(trans: {str: object}) -> str:
    """Condense the translation strings into a single report summary string"""
    summary = []
    if 'Wind' in trans and trans['Wind']:
        summary.append('Winds ' + trans['Wind'])
    if 'Visibility' in trans and trans['Visibility']:
        summary.append('Vis ' + trans['Visibility'][:trans['Visibility'].find(' (')].lower())
    if 'Temperature' in trans and trans['Temperature']:
        summary.append('Temp ' + trans['Temperature'][:trans['Temperature'].find(' (')])
    if 'Dewpoint' in trans and trans['Dewpoint']:
        summary.append('Dew ' + trans['Dewpoint'][:trans['Dewpoint'].find(' (')])
    if 'Altimeter' in trans and trans['Altimeter']:
        summary.append('Alt ' + trans['Altimeter'][:trans['Altimeter'].find(' (')])
    if 'Other' in trans and trans['Other']:
        summary.append(trans['Other'])
    if 'Clouds' in trans and trans['Clouds']:
        summary.append(trans['Clouds'].replace(' - Reported AGL', ''))
    return ', '.join(summary)


def taf(trans: {str: object}) -> str:
    """Condense the translation strings into a single forecast summary string"""
    summary = []
    if 'Wind' in trans and trans['Wind']:
        summary.append('Winds ' + trans['Wind'])
    if 'Visibility' in trans and trans['Visibility']:
        summary.append('Vis ' + trans['Visibility'][:trans['Visibility'].find(' (')].lower())
    if 'Altimeter' in trans and trans['Altimeter']:
        summary.append('Alt ' + trans['Altimeter'][:trans['Altimeter'].find(' (')])
    if 'Other' in trans and trans['Other']:
        summary.append(trans['Other'])
    if 'Clouds' in trans and trans['Clouds']:
        summary.append(trans['Clouds'].replace(' - Reported AGL', ''))
    if 'Wind-Shear' in trans and trans['Wind-Shear']:
        summary.append(trans['Wind-Shear'])
    if 'Turbulance' in trans and trans['Turbulance']:
        summary.append(trans['Turbulance'])
    if 'Icing' in trans and trans['Icing']:
        summary.append(trans['Icing'])
    return ', '.join(summary)
