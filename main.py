import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from app_web import run_web

if __name__ == "__main__":
    run_web()
