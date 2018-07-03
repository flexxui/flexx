"""
Script to deploy the docs on the site server. Intended to be run from CI/CD.
"""

import os
import io
import sys
import zipfile

import requests


DEPLOYER_ACCESS_TOKEN = os.getenv('DEPLOYER_ACCESS_TOKEN_SITE')
SITE_DIR = os.path.dirname(os.path.abspath(__file__))


def deploy():
    imagename = 'flexxdemo:1'
    
    # Zip it up
    f = io.BytesIO()
    with zipfile.ZipFile(f, 'w') as zf:
        for name in os.listdir(SITE_DIR):
            fullname = os.path.join(SITE_DIR, name)
            if os.path.isfile(fullname):
                bb = open(fullname, 'rb').read()
                zf.writestr(os.path.relpath(fullname, SITE_DIR), bb)
    
    # POST
    url = 'https://deploy.canpute.com/{}/{}'.format(imagename, DEPLOYER_ACCESS_TOKEN)
    r = requests.post(url, data=f.getvalue())
    if r.status_code != 200:
        raise RuntimeError('Publish failed: ' + r.text)
    else:
        print('Publish succeeded, ' + r.text)


if __name__ == '__main__':
    deploy()
