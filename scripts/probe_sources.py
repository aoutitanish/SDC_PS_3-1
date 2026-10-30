"""
Probe all target data sources for accessibility, rate limits, and available datasets.
"""
import requests
import sys
import time
import json

sys.stdout.reconfigure(encoding='utf-8')

HEADERS = {'User-Agent': 'Mozilla/5.0 (KrishiMitra Research Bot; educational use)'}
TIMEOUT = 25

results = {}

def probe(name, url, params=None, method='GET'):
    try:
        r = requests.request(method, url, params=params, headers=HEADERS, timeout=TIMEOUT)
        result = {'status': r.status_code, 'ok': r.ok, 'size': len(r.content), 'content_type': r.headers.get('Content-Type','')}
        if r.ok and 'json' in r.headers.get('Content-Type',''):
            try:
                d = r.json()
                result['json_keys'] = list(d.keys())[:6]
            except Exception:
                pass
        print(f"  [{name}] {r.status_code} | size={len(r.content)} | ct={r.headers.get('Content-Type','')[:50]}")
        return result
    except Exception as e:
        print(f"  [{name}] ERROR: {e}")
        return {'error': str(e)}

# --- NASA POWER (Monthly Agroclimatology) ---
print("\n=== NASA POWER (Monthly AG) ===")
r = probe('nasa_power_monthly', 'https://power.larc.nasa.gov/api/temporal/monthly/point', {
    'parameters': 'T2M,PRECTOTCORR,RH2M,WS2M,T2M_MAX,T2M_MIN',
    'community': 'AG', 'longitude': '78.48', 'latitude': '17.38',
    'start': '2015', 'end': '2020', 'format': 'JSON'
})
results['nasa_power'] = r
time.sleep(2)

# --- NASA POWER (Climatology) ---
print("\n=== NASA POWER (Climatology) ===")
r2 = probe('nasa_power_clim', 'https://power.larc.nasa.gov/api/temporal/climatology/point', {
    'parameters': 'T2M,PRECTOTCORR,RH2M,WS2M',
    'community': 'AG', 'longitude': '78.48', 'latitude': '17.38',
    'format': 'JSON'
})
results['nasa_power_climatology'] = r2
time.sleep(2)

# --- SoilGrids v2.0 ---
print("\n=== SoilGrids v2.0 ===")
r3 = probe('soilgrids', 'https://rest.isric.org/soilgrids/v2.0/properties/query', {
    'lon': 78.48, 'lat': 17.38,
    'property': ['phh2o', 'nitrogen', 'clay', 'sand', 'silt', 'soc', 'bdod', 'cec'],
    'depth': '0-5cm', 'value': 'mean'
})
results['soilgrids'] = r3
time.sleep(2)

# --- DES/desagri portal ---
print("\n=== DES APY Portal ===")
r4 = probe('des_portal', 'https://data.desagri.gov.in/website/crops-apy-report-web')
results['des_portal'] = r4
time.sleep(2)

# --- Agmarknet ---
print("\n=== Agmarknet ===")
r5 = probe('agmarknet', 'https://agmarknet.gov.in/SearchCmmMkt.aspx')
results['agmarknet'] = r5
time.sleep(2)

# --- data.gov.in OGD platform ---
print("\n=== data.gov.in OGD ===")
r6 = probe('data_gov_in', 'https://data.gov.in/search/field_topic/Agriculture', {})
results['data_gov_in'] = r6
time.sleep(2)

# --- FAO FAOSTAT API ---
print("\n=== FAO FAOSTAT ===")
r7 = probe('fao_faostat', 'https://fenixservices.fao.org/faostat/api/v1/en/data/QCL', {
    'area': '100', 'element': '5510,5312,5419', 'item': '27,56,71,83,89', 'year': '2015,2016,2017,2018,2019,2020',
    'outputType': 'objects'
})
results['fao_faostat'] = r7
time.sleep(2)

# --- IMD ---
print("\n=== IMD ===")
r8 = probe('imd', 'https://mausam.imd.gov.in/')
results['imd'] = r8
time.sleep(2)

# --- ICAR ---
print("\n=== ICAR ===")
r9 = probe('icar', 'https://icar.org.in/')
results['icar'] = r9
time.sleep(2)

# --- ICAR NBSS&LUP ---
print("\n=== ICAR NBSS&LUP ===")
r10 = probe('icar_nbsslup', 'https://www.nbsslup.in/')
results['icar_nbsslup'] = r10
time.sleep(2)

print("\n\n=== SUMMARY ===")
for src, res in results.items():
    status = res.get('status', 'N/A')
    ok = res.get('ok', False)
    err = res.get('error', None)
    label = 'ACCESSIBLE' if ok else ('TIMEOUT/ERROR' if err else f'HTTP {status}')
    print(f"  {src:<30}: {label}")

with open('scripts/source_probe_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2)
print("\nResults saved to scripts/source_probe_results.json")
