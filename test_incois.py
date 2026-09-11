from providers.incois.adapter import download_incois_file

url = "https://incois.gov.in/thredds/fileServer/osf/ww3/rsmc_combined_ww3_20260910.nc"

result = download_incois_file(
    url,
    "data/raw/incois_test.nc",
)

print(result)