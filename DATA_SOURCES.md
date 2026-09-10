# DATA SOURCES

Use authoritative sources wherever possible and preserve provenance.

## INCOIS

### Ocean State Forecast
https://incois.gov.in/oceanservices/osfforecast.jsp

Relevant marine/ocean parameters can include:
- wind
- surface currents
- significant wave height
- swell
- wave period
- SST
- mixed layer depth
- D20
- chlorophyll and other ocean products

### INCOIS ERDDAP
https://erddap.incois.gov.in/erddap/

Dataset catalog:
https://erddap.incois.gov.in/erddap/tabledap/allDatasets.html

ERDDAP can provide programmatic spatial/time subsets. Verify the exact dataset ID, variables, units, timestamps and access before implementation.

### INCOIS PFZ Advisory
https://incois.gov.in/MarineFisheries/PfzAdvisory

PFZ WebGIS:
https://www.incois.gov.in/MarineFisheries/PfzWebGis

PFZ Geoportal:
https://incois.gov.in/geoportal/MFASPFZ/index.html

Do not call ORCA-generated candidate zones official PFZs.

### INCOIS Location Specific Forecast
https://incois.gov.in/oceanservices/LSF/index.html

### INCOIS Small Vessel Advisory
https://incois.gov.in/site/services/SVA_overview.jsp

Useful for future safety architecture.

## IMD

### Official API reference
https://api.imd.gov.in/public/api_reference.html

The API reference includes marine services such as:
- sea area bulletin
- coastal bulletin
- port warning
- fishermen warning
- cyclone information

Access requirements must be verified. Never hard-code credentials.

### IMD Marine Forecast
https://mausam.imd.gov.in/responsive/marine_forecast_3.php

## Geospatial

Survey of India:
https://surveyofindia.gov.in/pages/public-awareness

Use the most appropriate authoritative geospatial source for each layer.

## Source verification checklist

Before coding against a provider:

- verify official domain
- verify endpoint/dataset
- verify required access/registration
- verify variables
- verify units
- verify spatial resolution
- verify timestamp semantics
- verify forecast vs observation
- verify missing-value behavior
- preserve source URL and retrieval time
- do not claim live access if data is cached

## Cached data wording

Use:
`Source: INCOIS — Cached official data`

Do not use:
`Live INCOIS data`

unless the application actually retrieves it live at request time.
