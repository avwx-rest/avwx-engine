"""NOTAM static values."""

# Q Codes sourced from FAA apprendix
# https://www.faa.gov/air_traffic/publications/atpubs/notam_html/appendix_b.html
# https://www.notams.faa.gov/common/qcode/qcode23.html

SUBJECT = {
    "AA": "Minimum altitude",
    "AC": "Class B, C, D, or E Surface Area",
    "AD": "Air defense identification zone",
    "AE": "Control area",
    "AF": "Flight information region",
    "AH": "Upper control area",
    "AL": "Minimum usable flight level",
    "AN": "Area navigation route",
    "AO": "Oceanic control area",
    "AP": "Reporting point",
    "AR": "ATS route",
    "AT": "Terminal control area",
    "AU": "Upper flight information region",
    "AV": "Upper advisory area",
    "AX": "Significant point",
    "AZ": "Aerodrome traffic zone",
    "CA": "Air/ground facility",
    "CB": "Automatic dependent surveillance - broadcast",
    "CC": "Automatic dependent surveillance - contract",
    "CD": "Controller-pilot data link communications",
    "CE": "En route surveillance radar",
    "CF": "Operating frequncy",
    "CG": "Ground controlled approach system",
    "CL": "Selective calling system",
    "CM": "Surface movement radar",
    "CO": "Operations",
    "CP": "Precision approach radar",
    "CR": "Surveillance radar element of precision approach radar system",
    "CS": "Secondary surveillance radar",
    "CT": "Terminal area surveillance radar",
    "FA": "Aerodrome",
    "FB": "Friction measuring device",
    "FC": "Ceiling measurement equipment",
    "FD": "Docking system",
    "FE": "Oxygen",
    "FF": "Fire fighting and rescue",
    "FG": "Ground movement control",
    "FH": "Helicopter alighting area/platform",
    "FI": "Aircraft de-icing",
    "FJ": "Oils",
    "FL": "Landing direction indicator",
    "FM": "Meteorological service",
    "FO": "Fog dispersal system",
    "FP": "Heliport",
    "FS": "Snow removal equipment",
    "FT": "Transmissometer",
    "FU": "Fuel availability",
    "FW": "Wind direction indicator",
    "FZ": "Customs/immigration",
    "GA": "GNSS airfield-specific operations",
    "GB": "Optical landing system",
    "GC": "Transient maitenance",
    "GD": "Starter unit",
    "GE": "Soap",
    "GF": "Demineralized water",
    "GG": "Oxygen",
    "GH": "Oil",
    "GI": "Drag chutes",
    "GJ": "ASR",
    "GK": "Precision approach landing system",
    "GL": "FACSFAC",
    "GM": "Firing range",
    "GN": "Night vision google operations",
    "GO": "Warning area",
    "GP": "Arresting gear markers",
    "GQ": "Pulsating/steady visual approach slope indicator",
    "GR": "Diverse departure",
    "GS": "Nitrogen",
    "GT": "IFR take-off minimums and departure procedures",
    "GU": "De-ice",
    "GV": "Clear zone",
    "GW": "GNSS area-wide operations",
    "GX": "Runway distance remaining signs",
    "GY": "Helo pad",
    "GZ": "Base operations",
    "IC": "Instrument landing system",
    "ID": "DME associated with ILS",
    "IG": "Glide path",
    "II": "Inner marker",
    "IL": "Localizer",
    "IM": "Middle marker",
    "IN": "Localizer",
    "IO": "Outer marker",
    "IS": "ILS Category I",
    "IT": "ILS Category II",
    "IU": "ILS Category III",
    "IW": "Microwave landing system",
    "IX": "Locator, outer",
    "IY": "Locator, middle",
    "KK": "Volcanic activity",
    "LA": "Approach lighting system",
    "LB": "Aerodrome beacon",
    "LC": "Runway centre line lights",
    "LD": "Landing direction indicator lights",
    "LE": "Runway edge lights",
    "LF": "Sequenced flashing lights",
    "LG": "Pilot-controlled lighting",
    "LH": "High intensity runway lights",
    "LI": "Runway end identifier lights",
    "LJ": "Runway alignment indicator lights",
    "LK": "Category II components of approach lighting system",
    "LL": "Low intensity runway lights",
    "LM": "Medium intensity runway lights",
    "LP": "Precision approach path indicator",
    "LR": "All landing area lighting facilities",
    "LS": "Stopway lights",
    "LT": "Threshold lights",
    "LU": "Helicopter approach path indicator",
    "LV": "Visual approach slope indicator system",
    "LW": "Heliport lighting",
    "LX": "Taxiway centre line lights",
    "LY": "Taxiway edge lights",
    "LZ": "Runway touchdown zone lights",
    "MA": "Movement area",
    "MB": "Bearing strength",
    "MC": "Clearway",
    "MD": "Declared distances",
    "MG": "Taxiing guidance system",
    "MH": "Runway arresting gear",
    "MK": "Parking area",
    "MM": "Daylight markings",
    "MN": "Apron",
    "MO": "Stopbar",
    "MP": "Aircraft stands",
    "MR": "Runway",
    "MS": "Stopway",
    "MT": "Threshold",
    "MU": "Runway turning bay",
    "MW": "Strip/shoulder",
    "MX": "Taxiway",
    "MY": "Rapid exit taxiway",
    "NA": "All radio navigation facilities",
    "NB": "Nondirectional radio beacon",
    "NC": "DECCA",
    "ND": "Distance measuring equipment",
    "NF": "Fan marker",
    "NL": "Locator",
    "NM": "VOR/DME",
    "NN": "TACAN",
    "NO": "OMEGA",
    "NT": "VORTAC",
    "NV": "VOR",
    "NX": "Direction finding station",
    "OA": "Aeronautical information service",
    "OB": "Obstacle",
    "OE": "Aircraft entry requirements",
    "OL": "Obstacle lights",
    "OR": "Rescue coordination centre",
    "PA": "Standard instrument arrival",
    "PB": "Standard VFR arrival",
    "PC": "Contingency procedures",
    "PD": "Standard instrument departure",
    "PE": "Standard VFR departure",
    "PF": "Flow control procedure",
    "PH": "Holding procedure",
    "PI": "Instrument approach procedure",
    "PK": "VFR approach procedure",
    "PL": "Flight plan processing",
    "PM": "Aerodrome operating minima",
    "PN": "Noise operating restriction",
    "PO": "Obstacle clearance altitude and height",
    "PR": "Radio failure procedure",
    "PT": "Transition altitude or transition level",
    "PU": "Missed approach procedure",
    "PX": "Minimum holding altitude",
    "PZ": "ADIZ procedure",
    "RA": "Airspace reservation",
    "RD": "Danger area",
    "RM": "Military operating area",
    "RO": "Overflying",
    "RP": "Prohibited area",
    "RR": "Restricted area",
    "RT": "Temporary restricted area",
    "SA": "Automatic terminal information service",
    "SB": "ATS reporting office",
    "SC": "Area control centre",
    "SE": "Flight information service",
    "SF": "Aerodrome flight information service",
    "SL": "Flow control centre",
    "SO": "Oceanic area control centre",
    "SP": "Approach control service",
    "SS": "Flight service station",
    "ST": "Aerodrome control tower",
    "SU": "Upper area control centre",
    "SV": "VOLMET broadcast",
    "SY": "Upper advisory service",
    "TT": "MIJI",
    "WA": "Air display",
    "WB": "Aerobatics",
    "WC": "Captive balloon or kite",
    "WD": "Demolition of explosives",
    "WE": "Exercises",
    "WF": "Air refueling",
    "WG": "Glider flying",
    "WH": "Blasting",
    "WJ": "Banner/target towing",
    "WL": "Ascent of free balloon",
    "WM": "Missile, gun or rocket firing",
    "WO": "Laser activity",  # Encountered, non-standard
    "WP": "Parachute jumping exercise, paragliding, or hang gliding",
    "WR": "Radioactive materials or toxic chemicals",
    "WS": "Burning or blowing gas",
    "WT": "Mass movement of aircraft",
    "WU": "Unmanned aircraft",
    "WV": "Formation flight",
    "WW": "Significant volcanic activity",
    "WY": "Aerial survey",
    "WZ": "Model flying",
    "XX": "Unknown",
}

CONDITION = {
    "AC": "Withdrawn for maintenance",
    "AD": "Available for daylight operation",
    "AF": "Flight checked and found reliable",
    "AG": "Operating but ground checked only, awaiting flight check",
    "AH": "Hours of service changed",
    "AK": "Resumed normal operations",
    "AL": "Operative",
    "AM": "Military operations only",
    "AN": "Available for night operation",
    "AO": "Operational",
    "AP": "Available, prior permission required",
    "AR": "Available on request",
    "AS": "Unserviceable",
    "AU": "Not available",
    "AW": "Completely withdrawn",
    "AX": "Previously promulgated shutdown has been canceled",
    "CA": "Activated",
    "CC": "Completed",
    "CD": "Deactivated",
    "CE": "Erected",
    "CF": "Frequency changed to",
    "CG": "Downgraded to",
    "CH": "Changed",
    "CI": "Identification or radio call sign changed to",
    "CL": "Realigned",
    "CM": "Displaced",
    "CN": "Canceled",
    "CO": "Operating",
    "CP": "Operating on reduced power",
    "CR": "Temporarily replaced by",
    "CS": "Installed",
    "CT": "On test, do not use",
    "HA": "Braking action",
    "HB": "Friction coefficient",
    "HC": "Covered by compacted snow to depth of",
    "HD": "Covered by dry snow to a depth of",
    "HE": "Covered by water to a depth of",
    "HF": "Totally free of snow and ice",
    "HG": "Grass cutting in progress",
    "HH": "Hazard due to",
    "HI": "Covered by ice",
    "HJ": "Launch planned",
    "HK": "Bird migration in progress",
    "HL": "Snow clearance completed",
    "HM": "Marked by",
    "HN": "Covered by wet snow or slush to a depth of",
    "HO": "Obscured by snow",
    "HP": "Snow clearance in progress",
    "HQ": "Operation canceled",
    "HR": "Standing water",
    "HS": "Sanding in progress",
    "HT": "Approach according to signal area only",
    "HU": "Launch in progress",
    "HV": "Work completed",
    "HW": "Work in progress",
    "HX": "Concentration of birds",
    "HY": "Snow banks exist",
    "HZ": "Covered by frozen ruts and ridges",
    "LA": "Operating on auxiliary power supply",
    "LB": "Reserved for aircraft based therein",
    "LC": "Closed",
    "LD": "Unsafe",
    "LE": "Operating without auxiliary power supply",
    "LF": "Interference from",
    "LG": "Operating without identification",
    "LH": "Unserviceable for aircraft heavier than",
    "LI": "Closed to IFR operations",
    "LK": "Operating as a fixed light",
    "LL": "Usable for length and width",
    "LN": "Closed to all night operations",
    "LP": "Prohibited to",
    "LR": "Aircraft restricted to runways and taxiways",
    "LS": "Subject to interruption",
    "LT": "Limited to",
    "LV": "Closed to VFR operations",
    "LW": "Will take place",
    "LX": "Operating but caution advised due to",
    "XX": "Plain text following",
}

# Other codes sourced from Nav Canada transition docs
# https://www.navcanada.ca/en/briefing-on-the-transition-to-icao-notam-format.pdf

REPORT_TYPE = {
    "NOTAMN": "New",
    "NOTAMR": "Replace",
    "NOTAMC": "Cancel",
}

TRAFFIC_TYPE = {
    "I": "IFR",
    "V": "VFR",
    "IV": "IFR and VFR",
}

PURPOSE = {
    "N": "Immediate",
    "B": "Briefing",
    "O": "Flight Operations",
    "M": "Miscellaneous",
    "K": "Checklist",
}

SCOPE = {
    "A": "Aerodrome",
    "E": "En Route",
    "W": "Warning",
    "K": "Checklist",
}

# Additional codes sourced from FAA NOTAM contractions list
# https://www.notams.faa.gov/downloads/contractions.pdf

CODES = {
    "ABN": "Airport Beacon",
    "ABV": "Above",
    "ACC": "Area Control Center",
    "ACCUM": "Accumulate",
    "ACFT": "Aircraft",
    "ACR": "Air Carrier",
    "ACT": "Active",
    "ADJ": "Adjacent",
    "ADZD": "Advised",
    "AFD": "Airport Facility Directory",
    "AGL": "Above Ground Level",
    "ALS": "Approach Lighting System",
    "ALT": "Altitude",
    "ALTM": "Altimeter",
    "ALTN": "Alternate",
    "ALTNLY": "Alternately",
    "ALSTG": "Altimeter Setting",
    "AMDT": "Amendment",
    "AMGR": "Airport Manager",
    "AMOS": "Automatic Meteorological Observing System",
    "AP": "Airport",
    "APCH": "Approach",
    "AP LGT": "Airport Lighting",
    "APP": "Approach Control",
    "ARFF": "Aircraft Rescue and Fire Fighting",
    "ARR": "Arrive, Arrival",
    "ASOS": "Automatic Surface Observing System",
    "ASPH": "Asphalt",
    "ATC": "Air Traffic Control",
    "ATCCC": "Air Traffic Control Command Center",
    "ATIS": "Automatic Terminal Information Service",
    "AUTOB": "Automatic Weather Reporting System",
    "AUTH": "Authority",
    "AVBL": "Available",
    "AWOS": "Automatic Weather Observing/Reporting System",
    "AWY": "Airway",
    "AZM": "Azimuth",
    "BA FAIR": "Braking action fair",
    "BA NIL": "Braking action nil",
    "BA POOR": "Braking action poor",
    "BC": "Back Course",
    "BCN": "Beacon",
    "BERM": "Snowbank(s) Containing Earth/Gravel",
    "BLW": "Below",
    "BND": "Bound",
    "BRG": "Bearing",
    "BYD": "Beyond",
    "CAAS": "Class A Airspace",
    "CAT": "Category",
    "CBAS": "Class B Airspace",
    "CBSA": "Class B Surface Area",
    "CCAS": "Class C Airspace",
    "CCLKWS": "Counterclockwise",
    "CCSA": "Class C Surface Area",
    "CD": "Clearance Delivery",
    "CDAS": "Class D Airspace",
    "CDSA": "Class D Surface Area",
    "CEAS": "Class E Airspace",
    "CESA": "Class E Surface Area",
    "CFR": "Code of Federal Regulations",
    "CGAS": "Class G Airspace",
    "CHAN": "Channel",
    "CHG": "Change or Modification",
    "CIG": "Ceiling",
    "CK": "Check",
    "CL": "Centre Line",
    "CLKWS": "Clockwise",
    "CLR": "Clearance, Clear(s), Cleared to",
    "CLSD": "Closed",
    "CMB": "Climb",
    "CMSND": "Commissioned",
    "CNL": "Cancel",
    "CNTRLN": "Centerline",
    "COM": "Communications",
    "CONC": "Concrete",
    "CPD": "Coupled",
    "CRS": "Course",
    "CTC": "Contact",
    "CTL": "Control",
    "DALGT": "Daylight",
    "DCMSN": "Decommission",
    "DCMSND": "Decommissioned",
    "DCT": "Direct",
    "DEGS": "Degrees",
    "DEP": "Depart, Departure",
    "DEP PROC": "Departure Procedure",
    "DH": "Decision Height",
    "DISABLD": "Disabled",
    "DIST": "Distance",
    "DLA": "Delay or Delayed",
    "DLT": "Delete",
    "DLY": "Daily",
    "DME": "Distance Measuring Equipment",
    "DMSTN": "Demonstration",
    "DP": "Dewpoint Temperature",
    "DRFT": "Snowbank/s Caused by Wind Action",
    "DSPLCD": "Displaced",
    "E": "East",
    "EB": "Eastbound",
    "EFAS": "En Route Flight Advisory Service",
    "ELEV": "Elevation",
    "ENG": "Engine",
    "ENRT": "En Route",
    "ENTR": "Entire",
    "EXC": "Except",
    "FAC": "Facility or Facilities",
    "FAF": "Final Approach Fix",
    "FAN MKR": "Fan Marker",
    "FDC": "Flight Data Center",
    "FI/T": "Flight Inspection Temporay",
    "FI/P": "Flight Inspection Permanent",
    "FM": "From",
    "FNA": "Final Approach",
    "FPM": "Feet Per Minute",
    "FREQ": "Frequency",
    "FRH": "Fly Runway Heading",
    "FRI": "Friday",
    "FRZN": "Frozen",
    "FSS": "Automated/Flight Service Station",
    "FT": "Foot, Feet",
    "GC": "Ground Control",
    "GCA": "Ground Control Approach",
    "GCO": "Ground Communications Outlet",
    "GOVT": "Government",
    "GP": "Glide Path",
    "GPS": "Global Positioning System",
    "GRVL": "Gravel",
    "HAA": "Height Above Airport",
    "HAT": "Height Above Touchdown",
    "HDG": "Heading",
    "HEL": "Helicopter",
    "HELI": "Heliport",
    "HIRL": "High Intensity Runway Lights",
    "HIWAS": "Hazardous Inflight Weather Advisory Service",
    "HLDG": "Holding",
    "HOL": "Holiday",
    "HP": "Holding Pattern",
    "HR": "Hour",
    "IAF": "Initial Approach Fix",
    "IAP": "Instrument Approach Procedure",
    "INBD": "Inbound",
    "ID": "Identification",
    "IDENT": "Identify, Identifier, Identification",
    "IF": "Intermediate Fix",
    "ILS": "Instrument Landing System",
    "IM": "Inner Marker",
    "IMC": "Instrument Meteorological Conditions",
    "IN": "Inch, Inches",
    "INDEFLY": "Indefinitely",
    "INFO": "Information",
    "INOP": "Inoperative",
    "INSTR": "Instrument",
    "INT": "Intersection",
    "INTL": "International",
    "INTST": "Intensity",
    "IR": "Ice On Runway(s)",
    "KT": "Knots",
    "L": "Left",
    "LAA": "Local Airport Advisory",
    "LAT": "Latitude",
    "LAWRS": "Limited Aviation Weather Reporting Station",
    "LB": "Pound(s)",
    "LC": "Local Control",
    "LOC": "Local, Locally, Location",
    "LCTD": "Located",
    "LDA": "Localizer Type Directional Aid",
    "LGT": "Light or Lighting",
    "LGTD": "Lighted",
    "LIRL": "Low Intensity Runway Lights",
    "LLWAS": "Low Level Wind Shear Alert System",
    "LM": "Compass Locator at ILS Middle Marker",
    "LDG": "Landing",
    "LLZ": "Localizer",
    "LO": "Compass Locator at ILS Outer Marker",
    "LONG": "Longitude",
    "LRN": "Long Range Navigation",
    "LSR": "Loose Snow on Runway(s)",
    "LT": "Left Turn",
    "MAG": "Magnetic",
    "MAINT": "Maintain, Maintenance",
    "MALS": "Medium Intensity Approach Light System",
    "MALSF": "Medium Intensity Approach Light System with Sequenced Flashers",
    "MALSR": "Medium Intensity Approach Light System with Runway Alignment Indicator Lights",
    "MAPT": "Missed Approach Point",
    "MCA": "Minimum Crossing Altitude",
    "MDA": "Minimum Descent Altitude",
    "MEA": "Minimum En Route Altitude",
    "MED": "Medium",
    "MIN": "Minute(s)",
    "MIRL": "Medium Intensity Runway Lights",
    "MKR": "Marker",
    "MLS": "Microwave Landing System",
    "MM": "Middle Marker",
    "MNM": "Minimum",
    "MNT": "Monitor, Monitoring, or Monitored",
    "MOC": "Minimum Obstruction Clearance",
    "MON": "Monday",
    "MRA": "Minimum Reception Altitude",
    "MSA": "MinimumSafeAltitude,MinimumSectorAltitude",
    "MSAW": "Minimum Safe Altitude Warning",
    "MSG": "Message",
    "MSL": "Mean Sea Level",
    "MU": "Mu Meters",
    "MUD": "Mud",
    "MUNI": "Municipal",
    "N": "North",
    "NA": "Not Authorized",
    "NAV": "Navigation",
    "NB": "Northbound",
    "NDB": "Nondirectional Radio Beacon",
    "NE": "Northeast",
    "NGT": "Night",
    "NM": "Nautical Mile(s)",
    "NMR": "Nautical Mile Radius",
    "NONSTD": "Nonstandard",
    "NOPT": "No Procedure Turn Required",
    "NR": "Number",
    "NTAP": "Notice to Airmen Publication",
    "NW": "Northwest",
    "OBSC": "Obscured, Obscure, or Obscuring",
    "OBST": "Obstruction, Obstacle",
    "OM": "Outer Marker",
    "OPR": "Operate, Operator, or Operative",
    "OPS": "Operation(s)",
    "ORIG": "Original",
    "OTS": "Out of Service",
    "OVR": "Over",
    "PAEW": "Personnel and Equipment Working",
    "PAX": "Passenger(s)",
    "PAPI": "Precision Approach Path Indicator",
    "PAR": "Precision Approach Radar",
    "PARL": "Parallel",
    "PAT": "Pattern",
    "PCL": "Pilot Controlled Lighting",
    "PERM": "Permanent",
    "PJE": "Parachute Jumping Exercise",
    "PLA": "Practice Low Approach",
    "PLW": "Plow, Plowed",
    "PN": "Prior Notice Required",
    "PPR": "Prior Permission Required",
    "PRN": "Psuedo Random Noise",
    "PROC": "Procedure",
    "PROP": "Propeller",
    "PSR": "Packed Snow on Runway(s)",
    "PTCHY": "Patchy",
    "PTN": "Procedure Turn",
    "PVT": "Private",
    "RAIL": "Runway Alignment Indicator Lights",
    "RAMOS": "Remote Automatic Meteorological Observing System",
    "RCAG": "Remote Communication Air/Ground Facility",
    "RCL": "Runway Center Line",
    "RCLL": "Runway Center Line Lights",
    "RCO": "Remote Communication Outlet",
    "REC": "Receive or Receiver",
    "REIL": "Runway End Identifier Lights",
    "RELCTD": "Relocated",
    "REP": "Report",
    "RLLS": "Runway Lead-In Light System",
    "RMNDR": "Remainder",
    "RMK": "Remark(s)",
    "RNAV": "Area Navigation",
    "RPLC": "Replace",
    "RQRD": "Required",
    "RRL": "Runway Remaining Lights",
    "RSR": "En Route Surveillance Radar",
    "RSVN": "Reservation",
    "RT": "Right Turn",
    "RTE": "Route",
    "RTR": "Remote Transmitter/Receiver",
    "RTS": "Return to Service",
    "RUF": "Rough",
    "RVR": "Runway Visual Range",
    "RVRM": "Runway Visual Range Midpoint",
    "RVRR": "Runway Visual Range Rollout",
    "RVRT": "Runway Visual Range Touchdown",
    "RWY": "Runway",
    "S": "South",
    "SA": "Sand, Sanded",
    "SAT": "Saturday",
    "SAWRS": "Supplementary Aviation Weather Reporting Station",
    "SB": "Southbound",
    "SDF": "Simplified Directional Facility",
    "SE": "Southeast",
    "SFL": "Sequence Flashing Lights",
    "SIMUL": "Simultaneous or Simultaneously",
    "SIR": "PackedorCompactedSnowandIceonRunway(s)",
    "SKED": "Scheduled or Schedule",
    "SLR": "Slush on Runway(s)",
    "SN": "Snow",
    "SNBNK": "Snowbank/s Caused by Plowing (Windrow(s))",
    "SNGL": "Single",
    "SPD": "Speed",
    "SSALF": "Simplified Short Approach Lighting with Sequence Flashers",
    "SSALR": "Simplified Short Approach Lighting with Runway Alignment Indicator Lights",
    "SSALS": "Simplified Short Approach Lighting System",
    "SSR": "Secondary Surveillance Radar",
    "STA": "Straight-In Approach",
    "STAR": "Standard Terminal Arrival",
    "SUN": "Sunday",
    "SVC": "Service",
    "SVN": "Satellite Vehicle Number",
    "SW": "Southwest",
    "SWEPT": "Swept",
    "T": "Temperature",
    "TACAN": "Tactical Air Navigational Aid (Azimuth and DME)",
    "TAR": "Terminal Area Surveillance Radar",
    "TDWR": "Terminal Doppler Weather Radar",
    "TDZ": "Touchdown Zone",
    "TDZ LGT": "Touchdown Zone Lights",
    "TEMPO": "Temporary or Temporarily",
    "TFC": "Traffic",
    "TFR": "Temporary Flight Restriction",
    "TGL": "Touch-and-Go Landings",
    "THN": "Thin",
    "THR": "Threshold",
    "THRU": "Through",
    "THU": "Thursday",
    "TIL": "Until",
    "TKOF": "Takeoff",
    "TM": "Traffic Management",
    "TMPA": "Traffic Management Program Alert",
    "TRML": "Terminal",
    "TRNG": "Training",
    "TRSN": "Transition",
    "TSNT": "Transient",
    "TUE": "Tuesday",
    "TWR": "Airport Control Tower",
    "TWY": "Taxiway",
    "UAV": "Unmanned Air Vehicles",
    "UFN": "Until Further Notice",
    "UNAVBL": "Unavailable",
    "UNLGTD": "Unlighted",
    "UNMKD": "Unmarked",
    "UNMNT": "Unmonitored",
    "UNREL": "Unreliable",
    "UNUSBL": "Unusable",
    "VASI": "Visual Approach Slope Indicator System",
    "VDP": "Visual Descent Point",
    "VIA": "By Way Of",
    "VICE": "Instead/Versus",
    "VIS": "Visibility",
    "VMC": "Visual Meteorological Conditions",
    "VOL": "Volume",
    "VOR": "VHF Omni-Directional Radio Range",
    "VORTAC": "VOR and TACAN (Collocated)",
    "W": "West",
    "WB": "Westbound",
    "WED": "Wednesday",
    "WEF": "With Effect From",
    "WI": "Within",
    "WIE": "With Immediate Effect",
    "WKDAYS": "Monday through Friday",
    "WKEND": "Saturday and Sunday",
    "WND": "Wind",
    "WPT": "Waypoint",
    "WSR": "Wet Snow on Runway(s)",
    "WTR": "Water on Runway(s)",
    "WX": "Weather",
}
