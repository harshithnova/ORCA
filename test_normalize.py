from providers.incois.normalize import normalize_kochi_sample

result = normalize_kochi_sample(
    "data/raw/incois_test.nc",
    "data/normalized/kochi_incois.json",
    "https://incois.gov.in/thredds/fileServer/osf/ww3/rsmc_combined_ww3_20260910.nc",
)

print(result)