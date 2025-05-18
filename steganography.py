from PIL import Image

def encode_image(image_path, message, output_path):
    """
    Encodes a secret message into an image using LSB steganography.
    
    Parameters:
    - image_path: Path to the input image
    - message: Secret message to encode
    - output_path: Path to save the encoded image
    
    Returns:
    - Boolean indicating success or failure
    """
    try:
        # Open the image
        image = Image.open(image_path)
        
        # Convert to RGB if it's not already (required for proper steganography)
        if image.mode != 'RGB':
            print(f"Converting image from {image.mode} to RGB mode for better compatibility")
            image = image.convert('RGB')
            
        encoded = image.copy()
        width, height = image.size
        index = 0

        # Add a stopping delimiter to the message
        original_message = message
        message += "###"
        binary_message = ''.join([format(ord(i), "08b") for i in message])
        
        # Check if message can fit in the image
        max_capacity = width * height * 3
        if len(binary_message) > max_capacity:
            max_chars = max_capacity // 8
            print(f"Error: Message too large for this image. Max length: {max_chars} characters, your message: {len(original_message)} characters")
            return False

        print(f"Encoding message of {len(original_message)} characters ({len(binary_message)} bits)")
        print(f"Image capacity: {max_capacity} bits ({max_capacity // 8} characters)")
        
        # Encode the message
        modified_pixels = 0
        for row in range(height):
            for col in range(width):
                if index < len(binary_message):
                    # Get pixel values
                    pixel_value = image.getpixel((col, row))
                    
                    # Handle different pixel formats
                    if isinstance(pixel_value, int):  # Grayscale
                        # For grayscale, just modify the single value
                        new_value = (pixel_value & ~1) | int(binary_message[index])
                        encoded.putpixel((col, row), new_value)
                        index += 1
                        modified_pixels += 1
                    else:  # RGB or RGBA
                        try:
                            # Convert to list if tuple, or create new list if already a list
                            if isinstance(pixel_value, tuple):
                                pixel = list(pixel_value)
                            else:
                                # This handles cases where pixel_value might be another format
                                pixel = [p for p in pixel_value] if hasattr(pixel_value, '__iter__') else [pixel_value]
                            
                            # Modify least significant bit of each color channel (RGB only)
                            for i in range(min(3, len(pixel))):
                                if index < len(binary_message):
                                    old_bit = pixel[i] & 1
                                    new_bit = int(binary_message[index])
                                    
                                    if old_bit != new_bit:  # Only modify if needed
                                        pixel[i] = (pixel[i] & ~1) | new_bit
                                    
                                    index += 1
                            
                            # Set the modified pixel
                            encoded.putpixel((col, row), tuple(pixel))
                            modified_pixels += 1
                        except Exception as pixel_error:
                            print(f"Error modifying pixel ({col},{row}): {str(pixel_error)}")
                            continue
                
                if index >= len(binary_message):
                    break
            if index >= len(binary_message):
                break

        # Verify the message was properly encoded
        verification_success = verify_encoding(encoded, original_message)
        
        # Save the encoded image as PNG (force PNG format for reliability)
        encoded = encoded.convert('RGB')  # Ensure we're in RGB mode
        output_format = 'PNG'
        encoded.save(output_path, format=output_format)
        
        print(f"Message encoded successfully! Modified {modified_pixels} pixels.")
        print(f"Saved as {output_format} format for maximum compatibility.")
        
        if verification_success:
            print("Verification successful: message can be properly decoded.")
        else:
            print("Warning: Verification failed. The message may not decode properly.")
            
        return True
    
    except Exception as e:
        print(f"Error encoding message: {str(e)}")
        return False


def verify_encoding(encoded_image, original_message):
    """
    Verify that a message was properly encoded by trying to decode it
    
    Parameters:
    - encoded_image: PIL Image object with the encoded message
    - original_message: The original message that was encoded
    
    Returns:
    - Boolean indicating whether verification was successful
    """
    try:
        width, height = encoded_image.size
        binary_data = ""
        
        # Extract enough bits to cover the message plus delimiter
        total_bits_needed = (len(original_message) + 3) * 8  # +3 for delimiter
        
        # Extract bits from the image
        for row in range(height):
            for col in range(width):
                if len(binary_data) >= total_bits_needed:
                    break
                
                try:
                    pixel_value = encoded_image.getpixel((col, row))
                    
                    # Handle different pixel formats
                    if isinstance(pixel_value, int):  # Grayscale
                        binary_data += str(pixel_value & 1)
                    else:  # RGB or RGBA
                        # Convert to list safely
                        if isinstance(pixel_value, tuple):
                            pixel_list = list(pixel_value)
                        else:
                            # This handles cases where pixel_value might be another format
                            pixel_list = [p for p in pixel_value] if hasattr(pixel_value, '__iter__') else [pixel_value]
                            
                        for i in range(min(3, len(pixel_list))):
                            if len(binary_data) < total_bits_needed:
                                binary_data += str(pixel_list[i] & 1)
                except:
                    continue
            
            if len(binary_data) >= total_bits_needed:
                break
        
        # Convert binary data to characters
        decoded_message = ""
        for i in range(0, len(binary_data), 8):
            if i + 8 <= len(binary_data):
                byte = binary_data[i:i+8]
                decoded_message += chr(int(byte, 2))
                
                # Check for delimiter
                if decoded_message.endswith("###"):
                    break
        
        # Remove delimiter and compare with original message
        if "###" in decoded_message:
            decoded_message = decoded_message[:-3]
            return decoded_message == original_message
        
        return False
    
    except Exception as e:
        print(f"Verification error: {str(e)}")
        return False


def decode_image(image_path):
    """
    Decodes a secret message from an image with LSB steganography.
    
    Parameters:
    - image_path: Path to the image with hidden message
    
    Returns:
    - Decoded message or None if extraction failed
    """
    try:
        # Open the image
        image = Image.open(image_path)
        binary_data = ""
        
        # Get image dimensions
        width, height = image.size
        
        # Extract the least significant bit from each color channel
        for row in range(height):
            for col in range(width):
                try:
                    pixel_value = image.getpixel((col, row))
                    
                    # Handle different pixel formats
                    if isinstance(pixel_value, int):  # Grayscale
                        binary_data += str(pixel_value & 1)
                    else:  # RGB or RGBA
                        pixel_list = list(pixel_value)
                        for i in range(min(3, len(pixel_list))):  # Use only RGB channels
                            binary_data += str(pixel_list[i] & 1)
                except Exception as e:
                    print(f"Error extracting bit from pixel ({col}, {row}): {str(e)}")
                    continue  # Skip problematic pixels
                    
        # Debug information
        print(f"Extracted {len(binary_data)} bits from image")
        
        # Check if we have enough bits to decode
        if len(binary_data) < 8:
            print("Not enough bits extracted from image")
            return None
        
        # Convert binary data to characters
        decoded_message = ""
        
        # Try to find the delimiter in chunks to avoid processing the entire image
        for i in range(0, min(len(binary_data), 50000), 8):  # Limit to first 50,000 bits for efficiency
            if i + 8 <= len(binary_data):
                byte = binary_data[i:i+8]
                try:
                    char = chr(int(byte, 2))
                    decoded_message += char
                    
                    # Check for delimiter after adding each character
                    if len(decoded_message) >= 3 and decoded_message[-3:] == "###":
                        return decoded_message[:-3]
                except ValueError:
                    print(f"Error converting byte {byte} to character")
                    continue
        
        # If we've processed enough bits without finding a delimiter, 
        # check if there's any reasonable text
        if decoded_message and len(decoded_message) > 2:
            # Try to find any printable ASCII text
            printable_chars = [c for c in decoded_message if 32 <= ord(c) <= 126]
            if len(printable_chars) > len(decoded_message) * 0.5:  # If at least 50% is readable
                print("Found potentially valid message without delimiter")
                return ''.join(printable_chars)
            
        print("No valid hidden message found or message format is incorrect")
        return None
    
    except Exception as e:
        print(f"Error decoding message: {str(e)}")
        return None


def analyze_image_capacity(image_path):
    """
    Analyzes and returns the message capacity of an image for steganography.
    
    Parameters:
    - image_path: Path to the image
    
    Returns:
    - Dictionary with capacity information
    """
    try:
        import os
        image = Image.open(image_path)
        width, height = image.size
        
        # Calculate maximum bits available (3 bits per pixel - 1 in each RGB channel)
        total_bits = width * height * 3
        
        # Convert to character capacity (each char is 8 bits)
        max_chars = total_bits // 8
        
        # Account for the delimiter (3 characters)
        usable_chars = max_chars - 3
        
        return {
            "image_dimensions": f"{width}x{height}",
            "max_bits": total_bits,
            "max_characters": usable_chars,
            "file_size_kb": os.path.getsize(image_path) / 1024
        }
    
    except Exception as e:
        print(f"Error analyzing image capacity: {str(e)}")
        return None


# For command-line usage
if __name__ == "__main__":
    import sys
    import os
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Encode: python steganography.py encode <input_image> <output_image> <message>")
        print("  Decode: python steganography.py decode <image_with_message>")
        sys.exit(1)
    
    action = sys.argv[1].lower()
    
    if action == "encode" and len(sys.argv) >= 5:
        input_image = sys.argv[2]
        output_image = sys.argv[3]
        message = sys.argv[4]
        encode_image(input_image, message, output_image)
    
    elif action == "decode" and len(sys.argv) >= 3:
        image_path = sys.argv[2]
        message = decode_image(image_path)
        if message:
            print(f"Decoded message: {message}")
    
    else:
        print("Invalid arguments")
        print("Usage:")
        print("  Encode: python steganography.py encode <input_image> <output_image> <message>")
        print("  Decode: python steganography.py decode <image_with_message>")