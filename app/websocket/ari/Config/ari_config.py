import base64
ARI_HOST     = "3.0.91.201"
ARI_HTTPS_PORT = 8089
ARI_PORT     = 8088
ARI_USER     = "thanh"
ARI_PASSWORD = "1234"
ARI_APP      = "nixxis"

BASE_URL  = f"http://{ARI_HOST}:{ARI_PORT}/ari"
AUTH      = (ARI_USER, ARI_PASSWORD)
WS_URL    = f"ws://{ARI_HOST}:{ARI_PORT}/ari/events?app={ARI_APP}&subscribeAll=true"
AUTH_HDR  = f"Basic {base64.b64encode(f'{ARI_USER}:{ARI_PASSWORD}'.encode()).decode()}"
