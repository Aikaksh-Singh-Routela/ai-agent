# When you get a response from run_agent()
response = run_agent(user_query)

# Check if response contains an image
if response.startswith("IMAGE_RESULT:"):
    parts = response.replace("IMAGE_RESULT:", "").split("|")
    image_path = parts[0]
    prompt_used = parts[1] if len(parts) > 1 else ""
    
    # Display the image
    from PIL import Image
    img = Image.open(image_path)
    st.image(img, caption=f"Generated: {prompt_used}", use_container_width=True)
    
    # Add download button
    with open(image_path, "rb") as f:
        st.download_button("📥 Download Image", f, file_name="generated_image.png", mime="image/png")
else:
    st.markdown(response)