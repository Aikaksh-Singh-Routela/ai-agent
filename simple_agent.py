def generate_image(prompt):
    """Generate an image using AI Horde (completely free, no API key needed)"""
    try:
        print(f"🎨 Starting image generation for: '{prompt}'")
        
        # --- 1. PREPARE THE REQUEST ---
        from horde_sdk.ai_horde_api.apimodels import ImageGenerateAsyncRequest
        from horde_sdk.ai_horde_api.ai_horde_clients import AIHordeAPISimpleClient
        import time

        horde_client = AIHordeAPISimpleClient()
        
        # Create the request object
        # The 'r2' parameter tells the Horde to use a direct download URL for the result [citation:4][citation:9]
        generation_request = ImageGenerateAsyncRequest(
            prompt=prompt,
            nsfw=False,
            censor_nsfw=True,
            r2=True,  # Use R2 for a stable download link
            params={
                "width": 512,
                "height": 512,
                "steps": 25,
                "n": 1
            }
        )
        
        # --- 2. SUBMIT THE JOB ---
        print("📤 Submitting request to AI Horde...")
        initial_response = horde_client.submit_request(generation_request)
        
        # The job ID is what we need to check the status later
        job_id = initial_response.id_
        print(f"✅ Job submitted successfully. Job ID: {job_id}")
        
        # --- 3. POLL FOR COMPLETION ---
        from horde_sdk.ai_horde_api.apimodels import ImageGenerateCheckRequest
        
        print("⏳ Waiting for the AI Horde to process your request...")
        max_attempts = 45  # ~90 seconds max wait
        for attempt in range(max_attempts):
            # Wait a few seconds between checks [citation:3]
            time.sleep(2)
            
            # Create a request to check the status of our job
            check_request = ImageGenerateCheckRequest(job_id=job_id)
            check_response = horde_client.submit_request(check_request)
            
            # 'is_finished' is True when the job is done [citation:5]
            if check_response.is_finished:
                print(f"🎉 Job finished! Duration: {check_response.processing_time} seconds")
                break
            elif attempt >= max_attempts - 1:
                print("❌ Timeout: The request took too long.")
                return None
        
        # --- 4. RETRIEVE THE GENERATED IMAGE ---
        from horde_sdk.ai_horde_api.apimodels import ImageGenerateStatusRequest
        
        # Now we can get the full result with the image
        status_request = ImageGenerateStatusRequest(job_id=job_id)
        final_response = horde_client.submit_request(status_request)
        
        if final_response.generations and len(final_response.generations) > 0:
            # The SDK's generation object might have a `.img` attribute (Base64) or a `.url` if `r2=True` was used [citation:6][citation:9]
            if final_response.generations[0].img:
                print("📥 Processing image from Base64 data...")
                image_data = base64.b64decode(final_response.generations[0].img)
            elif final_response.generations[0].url:
                print(f"📥 Downloading image from URL: {final_response.generations[0].url}")
                img_response = requests.get(final_response.generations[0].url)
                img_response.raise_for_status()
                image_data = img_response.content
            else:
                print("❌ No image data found in the response.")
                return None

            # Save the image to a temporary file
            img = Image.open(BytesIO(image_data))
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            img.save(temp_file.name)
            print(f"✅ Image successfully generated and saved!")
            return temp_file.name
        else:
            print("❌ No generations found in the final response.")
            return None

    except Exception as e:
        print(f"🚨 An unexpected error occurred: {e}")
        return None