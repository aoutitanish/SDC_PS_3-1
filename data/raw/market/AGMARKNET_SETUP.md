# Official Agmarknet / data.gov.in API Integration Guide

## 1. Overview
The Government of India publishes daily APMC mandi wholesale price and arrival records via the Open Government Data (OGD) platform under the **Government Open Data License India (GODL-India) v1.0**.

- **Portal**: [https://data.gov.in](https://data.gov.in)
- **Resource Title**: Daily Agmarknet Price and Arrival Data
- **Resource ID**: `9ef84268-d588-465a-a308-a864a43d0070`
- **Base Endpoint**: `https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070`
- **Licensing**: Open for public, commercial, and research use with attribution.

---

## 2. Step-by-Step API Registration
Accessing the OGD API requires a valid registered API key:

1. **Visit the Registration Portal**:
   Navigate to [https://data.gov.in/user/register](https://data.gov.in/user/register).
2. **Complete User Details**:
   - Provide your name, email address, mobile number, and organization/individual classification.
   - Verify your email address via the one-time link/OTP sent by NIC.
3. **Obtain API Key**:
   - Log into [https://data.gov.in/user/login](https://data.gov.in/user/login).
   - Go to **My Account** -> **API Dashboard** / **Generate API Key**.
   - Copy the 64-character alphanumeric API key.
4. **Configure Environment Variable**:
   In PowerShell:
   ```powershell
   [System.Environment]::SetEnvironmentVariable('DATAGOV_API_KEY', 'your_actual_api_key_here', 'User')
   $env:DATAGOV_API_KEY = "your_actual_api_key_here"
   ```
   Or add to `.env`:
   ```bash
   DATAGOV_API_KEY=your_actual_api_key_here
   ```

---

## 3. API Limits and Responsible Ingestion Policy
- **Rate Limit**: Maximum 1 request per second recommended; throttled by NIC if exceeded.
- **Page Size**: Maximum 5,000 records per request (`limit=5000`).
- **Pagination**: Use `offset=0`, `offset=5000`, `offset=10000`, etc., until `offset + limit >= total`.
- **Filtering**:
  - Filter by commodity: `&filters[Commodity]=Wheat`
  - Filter by state: `&filters[State]=Punjab`
  - Filter by date: `&filters[Arrival_Date]=01/10/2026`

---

## 4. Preservation Schema & Integrity Rules
Any downstream ingestion script (e.g. `scripts/acquire_agmarknet_ogd.py` and `scripts/process_agmarknet_mandi.py`) MUST preserve the following canonical fields:

| Field Name | Type | Description | Unit / Format |
| :--- | :--- | :--- | :--- |
| `state` | string | State / UT name | Normalized title case |
| `district` | string | District name | Normalized title case |
| `market` | string | APMC Mandi market yard name | String |
| `commodity` | string | Commodity name as reported by mandi | String |
| `variety` | string | Variety reported | String |
| `grade` | string | Grade reported (FAQ, Medium, etc.) | String |
| `arrival_date` | string | Transaction/arrival date | `YYYY-MM-DD` |
| `min_price` | float | Minimum transaction price | INR / quintal |
| `max_price` | float | Maximum transaction price | INR / quintal |
| `modal_price` | float | Modal transaction price (most frequent) | INR / quintal |
| `price_unit` | string | Price unit | Always `INR/quintal` (explicit) |
| `source_metadata` | object | Source URL, resource ID, retrieval timestamp | JSON metadata |

### Strict Integrity Constraints:
1. **Never substitute MSP for Mandi Price**: Mandi price reflects actual supply/demand clearing; Minimum Support Price (MSP) is a central government price guarantee. Mixing them corrupts economic and predictive modeling.
2. **Validate Price Range**: Reject non-positive prices (`modal_price <= 0`) and extreme recording errors (`modal_price > 150000 INR/quintal` for standard field crops).
3. **Date Validation**: Standardize all date strings (`DD/MM/YYYY` -> `YYYY-MM-DD`). Reject dates in the future.
4. **No Synthetic Inflation**: Missing mandi dates must remain missing; do not interpolate or fabricate records.
