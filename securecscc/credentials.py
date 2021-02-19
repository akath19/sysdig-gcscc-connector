import os
import json


class Credentials(object):
    def sysdig_token(self):
        return os.environ['SYSDIG_TOKEN']

    def security_service_account_info(self):
        if os.environ.get('SECURITY_SERVICE_ACCOUNT_INFO') is None:
            return None
        else:
            return json.loads(os.environ['SECURITY_SERVICE_ACCOUNT_INFO'])

    def compute_service_account_info(self):
        return json.loads(os.environ['COMPUTE_SERVICE_ACCOUNT_INFO'])
