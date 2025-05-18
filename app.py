import streamlit as st
import os
from PIL import Image
import io
import base64
from steganography import encode_image, decode_image, analyze_image_capacity
from database import add_encoded_image, get_recent_images, get_stats

# Set page configuration
st.set_page_config(
    page_title="Image Steganography",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Main page
st.title("Image Steganography Tool")
st.markdown("""
This tool allows you to hide and reveal secret messages within images using steganography techniques.
The image appears normal to the human eye, but contains hidden data in the least significant bits of the pixel values.
""")

# Create necessary folders
os.makedirs('data/steganography', exist_ok=True)
os.makedirs('data/database', exist_ok=True)

# Tab selection
tab1, tab2 = st.tabs(["Encode Message", "Decode Message"])

# Encode Tab
with tab1:
    st.subheader("Encode a Secret Message")
    
    # Upload image
    uploaded_file = st.file_uploader("Upload an image to hide your message in", type=["png", "jpg", "jpeg"])
    
    if uploaded_file is not None:
        # Display original image
        image = Image.open(uploaded_file)
        st.image(image, caption="Original Image")
        
        # Image info and capacity
        image_width, image_height = image.size
        file_size_kb = len(uploaded_file.getvalue()) / 1024
        
        # Image capacity info
        with st.expander("Image Capacity Information"):
            # Save the uploaded file temporarily
            temp_path = f"data/steganography/temp_upload_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
                
            # Analyze capacity
            try:
                capacity = analyze_image_capacity(temp_path)
                if capacity:
                    st.info(f"""
                    **Image Dimensions:** {capacity['image_dimensions']}  
                    **Maximum Characters:** {capacity['max_characters']}  
                    **File Size:** {capacity['file_size_kb']:.2f} KB
                    """)
                    max_chars = capacity['max_characters']
                else:
                    max_chars = None
            except Exception as e:
                st.error(f"Error analyzing image capacity: {str(e)}")
                max_chars = None
        
        # Message input
        message = st.text_area("Enter your secret message to hide", height=150)
        
        # Output filename
        output_filename = st.text_input("Output filename (with extension)", "encoded_image.png")
        
        if st.button("Encode Message into Image"):
            if message:
                with st.spinner("Encoding message..."):
                    # Ensure the output directory exists
                    os.makedirs('data/steganography', exist_ok=True)
                    
                    # Save the uploaded file temporarily
                    temp_path = f"data/steganography/temp_upload_{uploaded_file.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Generate output path
                    output_path = os.path.join('data/steganography', output_filename)
                    
                    # Encode the message
                    success = encode_image(temp_path, message, output_path)
                    
                    if success:
                        # Save to database
                        try:
                            add_encoded_image(
                                original_filename=uploaded_file.name,
                                encoded_filename=output_filename,
                                encoded_path=output_path,
                                message=message,
                                image_width=image_width,
                                image_height=image_height,
                                file_size_kb=file_size_kb,
                                capacity_chars=max_chars,
                                original_path=temp_path,
                                is_successful=True
                            )
                        except Exception as e:
                            st.warning(f"Image encoded successfully, but failed to save to history: {str(e)}")
                        
                        # Display the encoded image
                        st.success(f"Message encoded successfully into {output_filename}!")
                        encoded_img = Image.open(output_path)
                        st.image(encoded_img, caption="Encoded Image")

                        
                        # Create download link
                        with open(output_path, "rb") as file:
                            btn = st.download_button(
                                label="Download Encoded Image",
                                data=file,
                                file_name=output_filename,
                                mime="image/png"
                            )
                            
                        # Show view history button
                        st.info("Your encoded image has been saved to history. Click the button below to view your history.")
                        if st.button("View History"):
                            st.switch_page("pages/history.py")
                    else:
                        # Record failed attempt
                        try:
                            add_encoded_image(
                                original_filename=uploaded_file.name,
                                encoded_filename=output_filename,
                                encoded_path="",
                                message=message,
                                image_width=image_width,
                                image_height=image_height,
                                file_size_kb=file_size_kb,
                                capacity_chars=max_chars,
                                original_path=temp_path,
                                is_successful=False,
                                notes="Encoding failed - message may be too large"
                            )
                        except:
                            pass
                            
                        st.error("Failed to encode message. The message may be too large for this image.")
            else:
                st.warning("Please enter a message to encode.")
    else:
        st.info("Please upload an image (PNG recommended for best results).")
        st.markdown("""
        **Tips for best results:**
        - Use PNG images rather than JPG/JPEG (which may lose data due to compression)
        - Larger images can store longer messages
        - The encoded image should be saved as PNG to preserve the hidden data
        """)

# Decode Tab
with tab2:
    st.subheader("Decode a Secret Message")
    
    # Upload image with hidden message
    uploaded_file = st.file_uploader("Upload an image with a hidden message", type=["png", "jpg", "jpeg"], key="decode_uploader")
    
    if uploaded_file is not None:
        # Display the image
        image = Image.open(uploaded_file)
        st.image(image, caption="Image with Hidden Message", use_container_width=True)
        
        decode_button = st.button("Decode Message")
        
        # Add debug option for advanced users
        with st.expander("Advanced Options"):
            show_debug = st.checkbox("Show debug information")
        
        if decode_button:
            with st.spinner("Decoding message..."):
                # Save the uploaded file temporarily
                temp_path = f"data/steganography/temp_decode_{uploaded_file.name}"
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Always create placeholder for debug information
                debug_placeholder = st.empty()
                if show_debug:
                    with debug_placeholder.container():
                        st.write("Decoding in progress...")
                
                # Check file format
                img_format = image.format
                if img_format != "PNG":
                    st.warning(f"Note: The image is in {img_format} format. PNG is recommended for reliable steganography.")
                
                # Decode the message
                try:
                    # Capture debug output
                    import io
                    import sys
                    old_stdout = sys.stdout
                    new_stdout = io.StringIO()
                    sys.stdout = new_stdout
                    
                    decoded_message = decode_image(temp_path)
                    
                    # Get debug output
                    sys.stdout = old_stdout
                    debug_output = new_stdout.getvalue()
                    
                    # Display debug information if requested
                    if show_debug and debug_output:
                        with debug_placeholder.container():
                            st.code(debug_output)
                    
                    # Display the decoded message
                    if decoded_message:
                        st.success("Message decoded successfully!")
                        st.text_area("Decoded message:", decoded_message, height=150)
                    else:
                        st.error("No valid hidden message found or the message format is incorrect.")
                        
                        # Show more detailed error info
                        if "Not enough bits" in debug_output:
                            st.info("The image doesn't appear to contain enough data to extract a message.")
                        elif "Error converting byte" in debug_output:
                            st.info("Found data that couldn't be converted to text characters.")
                        
                        st.info("Try using an image that was encoded using this tool and make sure you're using the PNG format.")
                except Exception as e:
                    st.error(f"Error during decoding: {str(e)}")
                
                # Clean up temp file
                try:
                    os.remove(temp_path)
                except:
                    pass
    else:
        st.info("Please upload an image that contains a hidden message.")

# Sidebar information
st.sidebar.header("Navigation")
st.sidebar.info("""
- **Home**: Encode and decode messages
- **History**: View your steganography history
""")

st.sidebar.header("About Steganography")
st.sidebar.info("""
**What is steganography?**

Steganography is the practice of hiding information within another message or physical object to avoid detection. In digital steganography, we hide data within digital files like images.

**How it works:**

This tool uses the Least Significant Bit (LSB) technique - slightly modifying the least important bit in each color channel to encode the message. The changes are typically invisible to the human eye.

**Usage tips:**
- Use PNG images for best results
- Larger images can store longer messages
- The encoded image should be saved as PNG (not JPG) to preserve the hidden data
""")

# Show database stats in sidebar
try:
    stats = get_stats()
    if stats and stats["total_images"] > 0:
        st.sidebar.header("Your Stats")
        st.sidebar.metric("Total Images", stats["total_images"])
        st.sidebar.metric("Characters Hidden", stats["total_message_chars"])
except:
    pass

# Footer
st.markdown("---")
st.caption("Image steganography can be used for secure communication or watermarking digital assets.")
