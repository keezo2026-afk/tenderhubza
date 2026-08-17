import json
from app.connectors.diagnostics import diagnose_https
from app.connectors.national.etenders import ETendersConnector
if __name__=="__main__":print(json.dumps(diagnose_https(ETendersConnector.BASE_URL+ETendersConnector.LIST_PATH).to_dict(),indent=2))
