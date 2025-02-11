#!/bin/bash
source venv/bin/activate
export PYTHONPATH=/Users/madhukarkumar/Dropbox/madhukar/git_repos/singlestore-kag:$PYTHONPATH
celery -A tasks worker --loglevel=info
