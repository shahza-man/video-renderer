import json
import base64
import os
import subprocess
from pathlib import Path

def create_video():
    print("🎬 Starting video creation...")
    
    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Load video data
    with open("video_data.json", "r") as f:
        data = json.loads(f.read())
    
    print(f"📊 Processing: {data.get('title', 'Unknown')}")
    
    # Save audio file
    audio_data = base64.b64decode(data['audio']['data'])
    audio_path = "temp_audio.mp3"
    with open(audio_path, "wb") as f:
        f.write(audio_data)
    
    # Save image files
    image_paths = []
    for i, img in enumerate(data['images']):
        img_data = base64.b64decode(img['data'])
        img_path = f"temp_image_{i:03d}.png"
        with open(img_path, "wb") as f:
            f.write(img_data)
        image_paths.append(img_path)
    
    print(f"📸 Saved {len(image_paths)} images")
    
    # Calculate timing
    duration = float(data['duration'])
    time_per_image = duration / len(image_paths)
    
    print(f"⏱️ Duration: {duration}s, {time_per_image:.2f}s per image")
    
    # Create image list for FFmpeg
    with open("image_list.txt", "w") as f:
        for img_path in image_paths:
            f.write(f"file '{img_path}'\n")
            f.write(f"duration {time_per_image}\n")
        # Repeat last image to ensure proper ending
        f.write(f"file '{image_paths[-1]}'\n")
    
    # Build video filename
    safe_filename = data.get('filename', 'video').replace(' ', '_')[:50]
    output_path = output_dir / f"{safe_filename}.mp4"
    
    # FFmpeg command for high-quality video
    cmd = [
        'ffmpeg', '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', 'image_list.txt',
        '-i', audio_path,
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-pix_fmt', 'yuv420p',
        '-r', '30',
        '-shortest',
        '-movflags', '+faststart',
        str(output_path)
    ]
    
    print("🎥 Running FFmpeg...")
    print(" ".join(cmd))
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("✅ Video created successfully!")
        
        # Get file size
        file_size = output_path.stat().st_size
        print(f"📁 Output: {output_path.name} ({file_size/1024/1024:.1f}MB)")
        
        # Create metadata file
        metadata = {
            "filename": output_path.name,
            "size_bytes": file_size,
            "size_mb": round(file_size/1024/1024, 2),
            "duration": duration,
            "images_count": len(image_paths),
            "title": data.get('title', 'Unknown')
        }
        
        with open(output_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
            
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg failed: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False
    
    finally:
        # Cleanup temp files
        for path in [audio_path, "image_list.txt"] + image_paths:
            if os.path.exists(path):
                os.remove(path)

if __name__ == "__main__":
    success = create_video()
    exit(0 if success else 1)
