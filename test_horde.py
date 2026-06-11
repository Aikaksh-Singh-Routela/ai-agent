import requests
import time

print("Submitting image request...")

r = requests.post(
    "https://aihorde.net/api/v2/generate/async",
    headers={"apikey": "NoZGwZL4_VLH-d6t1nOQBA", "Content-Type": "application/json"},
    json={"prompt": "cat", "params": {"width": 512, "height": 512, "steps": 20}}
)

print(f"Status: {r.status_code}")

if r.status_code == 202:
    job_id = r.json()["id"]
    print(f"Job ID: {job_id}")
    print("Checking status every 10 seconds...")
    
    for i in range(30):
        time.sleep(10)
        status = requests.get(f"https://aihorde.net/api/v2/generate/status/{job_id}")
        data = status.json()
        
        if data.get("done"):
            print("✅ Image ready!")
            print(data["generations"][0]["img"])
            break
        else:
            waiting = data.get("waiting", 0)
            processing = data.get("processing", 0)
            print(f"Waiting... (queue: {waiting}, processing: {processing})")
else:
    print("Failed to submit request")