"""
CRONUS DW Pipeline — Configuration
Environment variables override defaults. Never commit secrets.
"""
import os

BC_TENANT_ID     = os.getenv("BC_TENANT_ID", "a88d0b90-fa0a-4ae2-b07e-7b09a0ad5194")
BC_ENVIRONMENT   = os.getenv("BC_ENVIRONMENT", "Production")
BC_COMPANY_ID    = os.getenv("BC_COMPANY_ID", "bf21ad7c-f048-f111-b477-7ced8d259edd")
BC_CLIENT_ID     = os.getenv("BC_CLIENT_ID", "4a0712a6-fc97-4cbc-8435-882309e753f8")
BC_CLIENT_SECRET = os.getenv("BC_CLIENT_SECRET", "")

BC_API_BASE = (
    f"https://api.businesscentral.dynamics.com/v2.0"
    f"/{BC_TENANT_ID}/{BC_ENVIRONMENT}/api/v2.0"
    f"/companies({BC_COMPANY_ID})"
)
BC_TOKEN_URL = f"https://login.microsoftonline.com/{BC_TENANT_ID}/oauth2/v2.0/token"
BC_SCOPE = "https://api.businesscentral.dynamics.com/.default"

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

USE_SYNTHETIC = os.getenv("USE_SYNTHETIC", "false").lower() == "true"
