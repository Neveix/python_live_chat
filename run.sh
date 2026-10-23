source .venv/bin/activate
uvicorn src.main:app --host 127.0.0.1 --port 47116 --ws-ping-interval 0 --ws-ping-timeout 0
