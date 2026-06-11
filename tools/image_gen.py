import os
import requests
import time

AI_HORDE_API_KEY = os.getenv("AI_HORDE_API_KEY", "NoZGwZL4_VLH-d6t1nOQBA")

def generate_image(prompt: str) -> str:
    """Generate an image using AI Horde."""
    
    print(f"🎨 Generating image for prompt: {prompt}")
    
    # Submit the request
    submit_response = requests.post(
        "https://aihorde.net/api/v2/generate/async",
        headers={
            "apikey": AI_HORDE_API_KEY,
            "Content-Type": "application/json"
        },
        json={
            "prompt": prompt,
            "params": {
                "width": 512,
                "height": 512,
                "steps": 25,
                "cfg_scale": 7,
                "sampler_name": "k_euler"
            }
        }
    )
    
    print(f"📤 Submit response status: {submit_response.status_code}")
    
    if submit_response.status_code != 202:
        return f"Error submitting image request: {submit_response.text}"
    
    job_id = submit_response.json().get("id")
    print(f"🆔 Job ID: {job_id}")
    
    # Poll for completion (wait up to 2 minutes)
    for i in range(30):
        time.sleep(5)
        status_response = requests.get(
            f"https://aihorde.net/api/v2/generate/status/{job_id}"
        )
        data = status_response.json()
        
        if data.get("done"):
            img_url = data["generations"][0]["img"]
            print(f"✅ Image generated: {img_url[:50]}...")
            return img_url
        else:
            waiting = data.get("waiting", 0)
            processing = data.get("processing", 0)
            print(f"⏳ Waiting: {waiting}, Processing: {processing}")
    
    return "Image generation timed out. The AI Horde might be busy. Please try again later."