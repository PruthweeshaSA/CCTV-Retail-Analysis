import cv2
import os

def downsample_video(input_path, output_path, target_fps=0.2):
    """
    Downsample a video to a target frame rate.
    
    Args:
        input_path: Path to input video file
        output_path: Path to output video file
        target_fps: Target frames per second (default: 0.2 = 1 frame every 5 seconds)
    """
    # Open the input video
    cap = cv2.VideoCapture(input_path)
    
    if not cap.isOpened():
        print(f"Error: Could not open video file {input_path}")
        return
    
    # Get video properties
    original_fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"Original FPS: {original_fps}")
    print(f"Target FPS: {target_fps}")
    print(f"Resolution: {width}x{height}")
    print(f"Total frames in input: {total_frames}")
    
    # Calculate frame interval
    frame_interval = int(original_fps / target_fps)
    print(f"Taking every {frame_interval}th frame")
    
    # Define codec and create VideoWriter
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, target_fps, (width, height))
    
    frame_count = 0
    saved_count = 0
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            break
        
        # Save frame if it matches our interval
        if frame_count % frame_interval == 0:
            out.write(frame)
            saved_count += 1
            print(f"Saved frame {saved_count} (original frame {frame_count})")
        
        frame_count += 1
    
    # Release resources
    cap.release()
    out.release()
    
    print(f"\nDownsampling complete!")
    print(f"Output frames: {saved_count}")
    print(f"Output saved to: {output_path}")

# Example usage
if __name__ == "__main__":
    input_video = "input11.mp4"  # Change this to your input video path
    output_video = "input11_downsampled.mp4"  # Change this to your desired output path
    
    downsample_video(input_video, output_video, target_fps=0.2)