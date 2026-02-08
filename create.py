import requests
import json
import re
import subprocess
import os
import time
import base64
import asyncio
import random
from pathlib import Path

# Import edge-tts for TTS generation
import edge_tts

# API Configuration
API_URL = "http://localhost:8017/v1/chat/completions"
API_KEY = None  # Set if needed

# Output directory
BASE_OUTPUT_DIR = Path("output_videos")

# TTS Voices
VOICE_VIDEO1 = "en-US-MichelleNeural"  # dialog[0]
VOICE_VIDEO2 = "en-US-AnaNeural"       # dialog[1]

# Transition settings
TRANSITION_TYPE = "slideleft"
TRANSITION_DURATION = 1.0

# Custom greenscreen transition settings
CUSTOM_TRANSITION_VIDEO = Path("transisi-custom/sample_with_audio1.mp4")
GREENSCREEN_COLOR = "0x1efb02"  # Bright green
GREENSCREEN_OVERLAP_V1 = 0.4  # Overlap 0.4s with end of video1

# Transition buffer (slowmo zone at end of video1)
TRANSITION_BUFFER_DURATION = 1.2  # seconds of buffer for transition overlap

# Swoosh sound for video1->video2 merge transition
SWOOSH_SOUND = Path("transisi-custom/swoosh-2-1s.mp3")

# Trigger overlay settings (greenscreen animations for video2)
TRIGGER_OVERLAYS = {
    "like": Path("trigger/like-greenscreen_1080p60_2.5x.mp4"),
    "subscribe": Path("trigger/subscribe-greenscreen_1080p60_2.5x.mp4"),
    "comment": Path("trigger/comment-greenscreen_1080p60_2.5x.mp4"),
    "share": Path("trigger/share-greenscreen_1080p60_2.5x.mp4"),
}
TRIGGER_POSITION_Y_OFFSET = 150  # pixels from bottom

# Backsound settings
MUSIC_DIR = Path("music")
BACKSOUND_VOLUME = 0.15  # 15% volume for background music


# ============================================================================
# TREE LOGGER - Structured Log Output
# ============================================================================

class TreeLogger:
    """Structured tree-style logger for clean output"""
    
    def __init__(self):
        self.indent_level = 0
        self.current_task = ""
        self.current_animal = ""
    
    def _prefix(self, is_last=False):
        """Generate tree prefix based on indent level"""
        if self.indent_level == 0:
            return ""
        return "│  " * (self.indent_level - 1) + ("└─ " if is_last else "├─ ")
    
    def _detail_prefix(self):
        """Prefix for nested details"""
        return "│  " * self.indent_level + "│  "
    
    def task_header(self, task_name, animal="", clothes="", vehicle=""):
        """Print task header like: Opening [Sloth - Leather Jacket - Convertible Car]"""
        self.current_task = task_name
        details = " - ".join(filter(None, [animal, clothes, vehicle]))
        header = f"{task_name.upper()}"
        if details:
            header += f" [{details}]"
        print(f"\n{'─' * 60}")
        print(header)
        print("─" * 60)
        self.indent_level = 0
    
    def step(self, name, index=None):
        """Start a new step like: ├─ Create image"""
        step_text = name
        if index:
            step_text += f" [{index}]"
        print(f"├─ {step_text}")
        self.indent_level = 1
    
    def success(self, url=None, path=None, extra=None):
        """Log success with optional details"""
        print(f"│  ├─ ✓ Sukses")
        if url:
            print(f"│  │  ├─ url: {url[:80]}{'...' if len(str(url)) > 80 else ''}")
        if path:
            print(f"│  │  ├─ path: {path}")
        if extra:
            for key, value in extra.items():
                print(f"│  │  ├─ {key}: {value}")
    
    def fail(self, attempt=None, error=None, retry=True):
        """Log failure with retry info"""
        if attempt:
            retry_text = f" [Kita coba lagi.. ({attempt})]" if retry else f" [Attempt {attempt}]"
        else:
            retry_text = " [Kita coba lagi..]" if retry else ""
        print(f"│  ├─ ✗ Gagal{retry_text}")
        if error:
            print(f"│  │  └─ error: {str(error)[:100]}")
    
    def info(self, key, value):
        """Log info detail"""
        print(f"│  │  ├─ {key}: {value}")
    
    def substep(self, name, success=True, details=None):
        """Log a substep with status"""
        status = "✓" if success else "✗"
        print(f"│  ├─ {status} {name}")
        if details:
            for key, value in details.items():
                print(f"│  │  ├─ {key}: {value}")
    
    def separator(self):
        """Print section separator"""
        print("\n" + "─" * 60 + "\n")

# Global logger instance
log = TreeLogger()

# Legacy print functions (for compatibility)
def print_header(text):
    log.step(text)

def print_success(text):
    print(f"│  ├─ ✓ {text}")

def print_error(text):
    print(f"│  ├─ ✗ {text}")

def print_info(label, text):
    print(f"│  │  ├─ {label}: {text}")


# ============================================================================
# RETRY DECORATOR
# ============================================================================

def retry_on_failure(max_retries=3, delay=2):
    """Decorator to retry function on failure"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    if result is not None and result != (None, None):
                        return result
                    if attempt < max_retries:
                        print_info("Retry", f"Attempt {attempt} failed, retrying in {delay}s...")
                        time.sleep(delay)
                except Exception as e:
                    if attempt < max_retries:
                        print_error(f"Attempt {attempt} failed: {e}")
                        print_info("Retry", f"Retrying in {delay}s... ({attempt}/{max_retries})")
                        time.sleep(delay)
                    else:
                        print_error(f"All {max_retries} attempts failed")
                        raise
            return None
        return wrapper
    return decorator


# ============================================================================
# TTS FUNCTIONS
# ============================================================================

async def generate_tts(text, voice, output_file, volume="+50%"):
    """Generate TTS audio using edge-tts with volume boost"""
    try:
        # Volume: +50% to make TTS louder over backsound
        communicate = edge_tts.Communicate(text, voice, rate="+0%", volume=volume)
        await communicate.save(str(output_file))
        print_success(f"TTS generated: {output_file.name} (vol: {volume})")
        return True
    except Exception as e:
        print_error(f"TTS generation failed: {e}")
        return False


def get_audio_duration(audio_file):
    """Get audio duration in seconds using ffprobe"""
    try:
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(audio_file)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except Exception as e:
        print_error(f"Failed to get audio duration: {e}")
        return 0


def get_video_duration(video_file):
    """Get video duration in seconds using ffprobe"""
    try:
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(video_file)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except Exception as e:
        print_error(f"Failed to get video duration: {e}")
        return 0


def add_audio_to_video(video_path, audio_path, output_path):
    """
    Add audio to video with smart synchronization:
    - If audio > video: Slow down video to match audio duration (smooth, no freeze)
    - If audio < video: Center audio in video timeline with proper padding
    """
    try:
        video_dur = get_video_duration(video_path)
        audio_dur = get_audio_duration(audio_path)
        
        print_info("Video duration", f"{video_dur:.2f}s ({video_dur*1000:.0f}ms)")
        print_info("Audio duration", f"{audio_dur:.2f}s ({audio_dur*1000:.0f}ms)")
        
        if audio_dur > video_dur:
            # Audio is longer - slow down video to match audio duration
            # Calculate PTS multiplier: audio_dur / video_dur
            pts_multiplier = audio_dur / video_dur
            print_info("Strategy", f"Slowing down video (PTS x{pts_multiplier:.3f}) to match {audio_dur:.2f}s")
            
            # Use setpts to slow down video, fps filter to ensure smooth 60fps output
            # Remove -shortest to prevent audio cutoff
            cmd = [
                'ffmpeg', '-y',
                '-i', str(video_path),
                '-i', str(audio_path),
                '-filter_complex', 
                f'[0:v]setpts={pts_multiplier}*PTS,fps=60[v]',
                '-map', '[v]',
                '-map', '1:a',
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '18',
                '-c:a', 'aac',
                '-b:a', '192k',
                '-t', str(audio_dur),  # Trim to exact audio duration
                str(output_path)
            ]
        else:
            # Video is longer - center audio with padding
            # Calculate delay for centering
            diff_ms = (video_dur - audio_dur) * 1000
            delay_ms = int(diff_ms / 2)
            end_pad_ms = int(diff_ms - delay_ms)  # Remaining padding at end
            
            print_info("Strategy", f"Centering audio with {delay_ms}ms delay")
            print_info("Timeline", f"Audio: {delay_ms}ms -> {delay_ms + audio_dur*1000:.0f}ms (video ends at {video_dur*1000:.0f}ms)")
            
            # Use adelay to center audio, apad to pad end, and trim to video duration
            cmd = [
                'ffmpeg', '-y',
                '-i', str(video_path),
                '-i', str(audio_path),
                '-filter_complex', 
                f'[1:a]adelay={delay_ms}|{delay_ms},apad=whole_dur={video_dur}[a]',
                '-map', '0:v',
                '-map', '[a]',
                '-c:v', 'copy',  # No re-encode needed for video
                '-c:a', 'aac',
                '-b:a', '192k',
                '-t', str(video_dur),  # Trim to exact video duration
                str(output_path)
            ]
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        # Verify output
        output_dur = get_video_duration(output_path)
        print_success(f"Audio added: {output_path.name} ({output_dur:.2f}s)")
        return True
        
    except subprocess.CalledProcessError as e:
        print_error(f"FFmpeg failed: {e.stderr[:500] if e.stderr else str(e)}")
        return False
    except Exception as e:
        print_error(f"Failed to add audio to video: {e}")
        return False


def add_audio_to_video_with_buffer(video_path, audio_path, output_path, buffer_duration=1.2):
    """
    Add audio to video with transition buffer zone at START.
    The first 'buffer_duration' seconds are left empty for transition overlay.
    Audio is centered within the effective duration AFTER the buffer.
    """
    try:
        video_dur = get_video_duration(video_path)
        audio_dur = get_audio_duration(audio_path)
        
        # Effective duration = total - buffer at start
        effective_dur = video_dur - buffer_duration
        
        print_info("Video total", f"{video_dur:.2f}s")
        print_info("Buffer zone", f"0 - {buffer_duration:.2f}s (first {buffer_duration}s empty)")
        print_info("Effective", f"{buffer_duration:.2f}s - {video_dur:.2f}s (for TTS)")
        print_info("Audio TTS", f"{audio_dur:.2f}s")
        
        # Calculate delay: buffer + centering within effective area
        if audio_dur >= effective_dur:
            # Audio fills effective area - start right after buffer
            delay_ms = int(buffer_duration * 1000)
            print_info("Placement", f"Audio fills area, starts at {delay_ms}ms")
        else:
            # Center audio in effective area (after buffer)
            center_delay = (effective_dur - audio_dur) / 2
            delay_ms = int((buffer_duration + center_delay) * 1000)
            print_info("Placement", f"Audio centered: delay {delay_ms}ms")
        
        audio_end_ms = delay_ms + int(audio_dur * 1000)
        print_info("Timeline", f"Buffer: 0-{int(buffer_duration*1000)}ms | TTS: {delay_ms}ms -> {audio_end_ms}ms")
        
        cmd = [
            'ffmpeg', '-y',
            '-i', str(video_path),
            '-i', str(audio_path),
            '-filter_complex', 
            f'[1:a]adelay={delay_ms}|{delay_ms},apad=whole_dur={video_dur}[a]',
            '-map', '0:v',
            '-map', '[a]',
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-t', str(video_dur),
            str(output_path)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        output_dur = get_video_duration(output_path)
        print_success(f"Audio added with buffer: {output_path.name} ({output_dur:.2f}s)")
        return True
        
    except subprocess.CalledProcessError as e:
        print_error(f"FFmpeg failed: {e.stderr[:500] if e.stderr else str(e)}")
        return False
    except Exception as e:
        print_error(f"Failed to add audio with buffer: {e}")
        return False


def add_audio_to_video_with_buffer_end(video_path, audio_path, output_path, buffer_duration=1.0):
    """
    Add audio to video with transition buffer zone at END.
    TTS is centered within effective duration (0 to total-buffer).
    Last 'buffer_duration' seconds are empty for transition.
    """
    try:
        video_dur = get_video_duration(video_path)
        audio_dur = get_audio_duration(audio_path)
        effective_dur = video_dur - buffer_duration
        
        print_info("Video total", f"{video_dur:.2f}s")
        print_info("Effective", f"0 - {effective_dur:.2f}s")
        print_info("Buffer END", f"{effective_dur:.2f}s - {video_dur:.2f}s (empty)")
        
        if audio_dur >= effective_dur:
            delay_ms = 0
        else:
            delay_ms = int((effective_dur - audio_dur) / 2 * 1000)
        
        print_info("TTS delay", f"{delay_ms}ms")
        
        cmd = [
            'ffmpeg', '-y',
            '-i', str(video_path),
            '-i', str(audio_path),
            '-filter_complex', 
            f'[1:a]adelay={delay_ms}|{delay_ms},apad=whole_dur={video_dur}[a]',
            '-map', '0:v', '-map', '[a]',
            '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
            '-t', str(video_dur),
            str(output_path)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print_success(f"Audio added with END buffer: {output_path.name}")
        return True
        
    except Exception as e:
        print_error(f"Failed: {e}")
        return False


def add_trigger_overlay(video_path, trigger_path, output_path, y_offset=150):
    """
    Add trigger greenscreen overlay to video.
    Trigger starts 4.5 seconds before video ends.
    Position: y_offset px from bottom, horizontally centered.
    """
    try:
        video_dur = get_video_duration(video_path)
        trigger_dur = get_video_duration(trigger_path)
        
        # Simple logic: trigger starts 4.5s before video ends
        start_time = video_dur - 4.5
        if start_time < 0:
            start_time = 0
        
        end_time = start_time + trigger_dur
        
        log.info("Video duration", f"{video_dur:.2f}s")
        log.info("Trigger duration", f"{trigger_dur:.2f}s")
        log.info("Trigger appears", f"{start_time:.2f}s - {end_time:.2f}s")
        
        # Use setpts to delay trigger start, preserving original speed
        filter_complex = (
            f"[1:v]colorkey={GREENSCREEN_COLOR}:0.3:0.2,scale=1080:-1,"
            f"setpts=PTS+{start_time}/TB,fps=60[overlay];"
            f"[0:v][overlay]overlay=(W-w)/2:H-h-{y_offset}:eof_action=pass[vout]"
        )
        
        cmd = [
            'ffmpeg', '-y',
            '-i', str(video_path),
            '-i', str(trigger_path),
            '-filter_complex', filter_complex,
            '-map', '[vout]',
            '-map', '0:a',
            '-c:v', 'libx264',
            '-profile:v', 'high',
            '-pix_fmt', 'yuv420p',
            '-preset', 'fast',
            '-crf', '18',
            '-c:a', 'copy',
            '-t', str(video_dur),
            str(output_path)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        log.success(path=str(output_path))
        return True
        
    except subprocess.CalledProcessError as e:
        log.fail(error=f"FFmpeg: {e.stderr[:200] if e.stderr else str(e)}")
        return False
    except Exception as e:
        log.fail(error=str(e))
        return False


def add_text_overlay(video_path, output_path, text, font_size=64, font_color="white", 
                     y_start=100, line_height=80, box_color="black@0.6", max_chars_per_line=28):
    """Add multi-line text overlay to video at top position"""
    try:
        log.step("Add Text Overlay")
        log.info("Text", f'"{text[:50]}..."' if len(text) > 50 else f'"{text}"')
        
        # Split text into multiple lines (word wrap)
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line + " " + word) <= max_chars_per_line:
                current_line = (current_line + " " + word).strip()
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        
        log.info("Lines", f"{len(lines)} lines")
        
        # Build filter with multiple drawtext
        filter_parts = []
        for i, line in enumerate(lines):
            y = y_start + (i * line_height)
            escaped_line = line.replace("'", "\\'").replace(":", "\\:")
            filter_parts.append(
                f"drawtext=text='{escaped_line}':"
                f"fontsize={font_size}:fontcolor={font_color}:"
                f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
                f"x=(w-text_w)/2:y={y}:"
                f"box=1:boxcolor={box_color}:boxborderw=15"
            )
        
        filter_complex = ",".join(filter_parts)
        
        cmd = [
            'ffmpeg', '-y',
            '-i', str(video_path),
            '-vf', filter_complex,
            '-c:v', 'libx264',
            '-profile:v', 'high',
            '-pix_fmt', 'yuv420p',
            '-preset', 'fast',
            '-crf', '18',
            '-c:a', 'copy',
            str(output_path)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        log.success(path=str(output_path))
        return True
        
    except subprocess.CalledProcessError as e:
        log.fail(error=f"FFmpeg: {e.stderr[:200] if e.stderr else str(e)}")
        return False
    except Exception as e:
        log.fail(error=str(e))
        return False


def add_backsound(video_path, output_path, volume=0.15):
    """Add random background music from music folder to video"""
    try:
        # Get random music file
        music_files = list(MUSIC_DIR.glob("*.mp3"))
        if not music_files:
            log.fail(error="No music files found in music folder")
            return False
        
        random_music = random.choice(music_files)
        video_dur = get_video_duration(video_path)
        
        log.step("Add Backsound")
        log.info("Music", random_music.name)
        log.info("Volume", f"{volume*100:.0f}%")
        
        # Mix backsound with fade out at end
        fade_start = video_dur - 3
        filter_complex = (
            f"[1:a]volume={volume},afade=t=out:st={fade_start}:d=3[music];"
            f"[0:a][music]amix=inputs=2:duration=first:dropout_transition=3[aout]"
        )
        
        cmd = [
            'ffmpeg', '-y',
            '-i', str(video_path),
            '-stream_loop', '-1',  # Loop music if shorter
            '-i', str(random_music),
            '-filter_complex', filter_complex,
            '-map', '0:v',
            '-map', '[aout]',
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-t', str(video_dur),
            str(output_path)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        log.success(path=str(output_path))
        return True
        
    except subprocess.CalledProcessError as e:
        log.fail(error=f"FFmpeg: {e.stderr[:200] if e.stderr else str(e)}")
        return False
    except Exception as e:
        log.fail(error=str(e))
        return False


# ============================================================================
# FILE DOWNLOAD
# ============================================================================

def download_file(url, output_path):
    """Download file from URL"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print_success(f"Downloaded to {output_path}")
        return True
    except Exception as e:
        print_error(f"Download failed: {e}")
        return False


# ============================================================================
# IMAGE & VIDEO GENERATION (from generate-advanced-test.py)
# ============================================================================

@retry_on_failure(max_retries=3, delay=2)
def generate_image(prompt):
    """Generate image from prompt"""
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"

    payload = {
        "model": "grok-imagine-0.9",
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}]
            }
        ]
    }

    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()

        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            
            match = re.search(r'!\[Generated Image\]\((http://localhost:8017/images/[^)]+)\)', content)
            if match:
                image_url = match.group(1)
                print_success("Image generated")
                print_info("URL", image_url)
                return image_url
            else:
                print_error("No image URL found in response")
                return None
        else:
            print_error("No content generated")
            return None
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {e}")
        return None


@retry_on_failure(max_retries=3, delay=2)
def edit_image(prompt, image_url):
    """Edit image with prompt - returns (image_url, content_type)"""
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"

    payload = {
        "model": "grok-4.1-thinking",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ]
    }

    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()

        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            
            # Try to extract image URL
            patterns = [
                r'!\[Generated Image\]\((http://localhost:8017/images/[^)]+\.jpg)\)',
                r'src="(http://localhost:8017/images/[^"]+\.jpg)"',
                r'(http://localhost:8017/images/[^\s\)\"]+\.jpg)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, content)
                if match:
                    url = match.group(1).rstrip('"')
                    print_success("Image edited")
                    print_info("URL", url)
                    return url, 'image'
            
            print_error("No image URL found")
            return None, None
        else:
            print_error("No content generated")
            return None, None
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {e}")
        return None, None


@retry_on_failure(max_retries=3, delay=2)
def generate_video(prompt, image_url):
    """Generate video from image - returns (video_id, video_url)"""
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"

    payload = {
        "model": "grok-imagine-0.9",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ]
    }

    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()

        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            
            # Extract video URL and ID
            patterns = [
                r'src="(http://localhost:8017/images/users-[^"]+generated_video\.mp4)"',
                r'(http://localhost:8017/images/users-[^\s\)\"]+generated_video\.mp4)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, content)
                if match:
                    video_url = match.group(1).rstrip('"')
                    # Extract video ID from URL
                    id_match = re.search(r'generated-([a-f0-9\-]+)-generated_video', video_url)
                    video_id = id_match.group(1) if id_match else "unknown"
                    
                    print_success("Video generated")
                    print_info("ID", video_id)
                    print_info("URL", video_url)
                    return video_id, video_url
            
            print_error("No video URL found")
            return None, None
        else:
            print_error("No content generated")
            return None, None
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {e}")
        return None, None


@retry_on_failure(max_retries=3, delay=3)
def upscale_video(video_id):
    """Upscale video to HD quality using API"""
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    
    payload = {"video_id": video_id}
    upscale_url = "http://localhost:8017/v1/videos/upscale"
    
    try:
        print_info("Processing", "Upscaling to HD (this may take 1-2 minutes)...")
        response = requests.post(upscale_url, headers=headers, data=json.dumps(payload), timeout=180)
        response.raise_for_status()
        result = response.json()
        
        if "hd_media_url" in result:
            hd_url = result["hd_media_url"]
            print_success("Video upscaled to HD")
            print_info("HD URL", hd_url)
            return hd_url
        else:
            print_error("No HD URL in response")
            return None
    except requests.exceptions.RequestException as e:
        print_error(f"Upscale failed: {e}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print_info("Details", e.response.text[:200])
        return None


def convert_to_60fps(input_path, output_path, target_width=1080, target_height=1920, target_fps=60):
    """Convert video to 1080x1920 60fps using ffmpeg - FULL SCREEN (no black bars)"""
    try:
        # Video filter: scale UP to cover entire frame, then crop to exact size
        vf = f"scale={target_width}:{target_height}:force_original_aspect_ratio=increase,crop={target_width}:{target_height},setsar=1,fps={target_fps}"
        
        cmd = [
            'ffmpeg', '-y', '-i', str(input_path),
            '-vf', vf,
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '18',
            '-c:a', 'aac',
            '-b:a', '192k',
            str(output_path)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        print_success(f"Converted to {target_width}x{target_height} {target_fps}fps (FULL SCREEN)")
        return True
    except Exception as e:
        print_error(f"Conversion failed: {e}")
        return False


def slowmo_video(input_path, output_path, target_duration):
    """
    Slow down entire video evenly to reach target duration.
    Used to create transition buffer zone at end of video.
    """
    try:
        video_dur = get_video_duration(input_path)
        
        if target_duration <= video_dur:
            print_info("Slowmo", "No slowmo needed, copying video")
            import shutil
            shutil.copy(input_path, output_path)
            return True
        
        # Calculate PTS multiplier for slowmo
        pts_multiplier = target_duration / video_dur
        
        print_info("Original", f"{video_dur:.2f}s")
        print_info("Target", f"{target_duration:.2f}s")
        print_info("Slowmo", f"{pts_multiplier:.3f}x (slower)")
        
        cmd = [
            'ffmpeg', '-y',
            '-i', str(input_path),
            '-filter_complex',
            f'[0:v]setpts={pts_multiplier}*PTS,fps=60[v]',
            '-map', '[v]',
            '-c:v', 'libx264',
            '-profile:v', 'high',
            '-pix_fmt', 'yuv420p',
            '-preset', 'medium',
            '-crf', '18',
            str(output_path)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        output_dur = get_video_duration(output_path)
        print_success(f"Slowmo applied: {output_path.name} ({output_dur:.2f}s)")
        return True
        
    except Exception as e:
        print_error(f"Slowmo failed: {e}")
        return False


def merge_with_transition(video1_path, video2_path, output_path, transition="smoothright", duration=1.0, swoosh_sound=None):
    """
    Merge two videos with xfade transition.
    Uses acrossfade for audio and mixes swoosh sound during transition.
    """
    try:
        # Get durations
        v1_duration = get_video_duration(video1_path)
        v2_duration = get_video_duration(video2_path)
        
        print_info("Video 1", f"{v1_duration:.2f}s")
        print_info("Video 2", f"{v2_duration:.2f}s")
        print_info("Transition", f"{transition} ({duration}s)")
        
        # xfade offset
        offset = v1_duration - duration
        expected_dur = v1_duration + v2_duration - duration
        
        # Build filter complex
        if swoosh_sound and Path(swoosh_sound).exists():
            print_info("Swoosh", f"{Path(swoosh_sound).name}")
            # With swoosh: mix swoosh sound during transition
            # Delay swoosh to start at transition point
            swoosh_delay_ms = int(offset * 1000)
            filter_complex = (
                f'[0:v][1:v]xfade=transition={transition}:duration={duration}:offset={offset}[vout];'
                f'[0:a][1:a]acrossfade=d={duration}:c1=tri:c2=tri[amix];'
                f'[2:a]adelay={swoosh_delay_ms}|{swoosh_delay_ms},volume=0.5[swoosh];'
                f'[amix][swoosh]amix=inputs=2:duration=first[aout]'
            )
            cmd = [
                'ffmpeg', '-y',
                '-i', str(video1_path),
                '-i', str(video2_path),
                '-i', str(swoosh_sound),
                '-filter_complex', filter_complex,
                '-map', '[vout]',
                '-map', '[aout]',
                '-c:v', 'libx264',
                '-profile:v', 'high',
                '-pix_fmt', 'yuv420p',
                '-preset', 'medium',
                '-crf', '18',
                '-r', '60',
                '-c:a', 'aac',
                '-b:a', '192k',
                str(output_path)
            ]
        else:
            # Without swoosh
            cmd = [
                'ffmpeg', '-y',
                '-i', str(video1_path),
                '-i', str(video2_path),
                '-filter_complex', 
                f'[0:v][1:v]xfade=transition={transition}:duration={duration}:offset={offset}[vout];'
                f'[0:a][1:a]acrossfade=d={duration}:c1=tri:c2=tri[aout]',
                '-map', '[vout]',
                '-map', '[aout]',
                '-c:v', 'libx264',
                '-profile:v', 'high',
                '-pix_fmt', 'yuv420p',
                '-preset', 'medium',
                '-crf', '18',
                '-r', '60',
                '-c:a', 'aac',
                '-b:a', '192k',
                str(output_path)
            ]
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        output_dur = get_video_duration(output_path)
        print_success(f"Merged with '{transition}': {output_path.name} ({output_dur:.2f}s)")
        return True
        
    except subprocess.CalledProcessError as e:
        print_error(f"Merge failed: {e.stderr[:500] if e.stderr else str(e)}")
        return False
    except Exception as e:
        print_error(f"Video merge failed: {e}")
        return False


def merge_with_greenscreen_transition(video1_path, video2_path, output_path, 
                                       transition_video=None, greenscreen_color="0x1efb02",
                                       overlap_v1=0.4):
    """
    Merge two videos with custom greenscreen transition.
    - overlap_v1: How much of video1's end is overlapped by transition
    - Rest of transition overlaps video2's start
    """
    try:
        if transition_video is None:
            transition_video = CUSTOM_TRANSITION_VIDEO
        
        v1_dur = get_video_duration(video1_path)
        v2_dur = get_video_duration(video2_path)
        tr_dur = get_video_duration(transition_video)
        
        overlap_v2 = tr_dur - overlap_v1
        
        print_info("Video 1", f"{v1_dur:.2f}s")
        print_info("Video 2", f"{v2_dur:.2f}s")
        print_info("Transition", f"{tr_dur:.2f}s (overlap V1: {overlap_v1:.2f}s, V2: {overlap_v2:.2f}s)")
        
        # Timeline:
        # 1. Video1[0 to v1_dur-overlap_v1] = video1 only
        # 2. Video1 last overlap_v1 + transition first overlap_v1 (chromakey on v1)
        # 3. Video2 first overlap_v2 + transition rest (chromakey on v2)
        # 4. Video2[overlap_v2 to end] = video2 only
        
        cmd = [
            'ffmpeg', '-y',
            '-i', str(video1_path),
            '-i', str(video2_path), 
            '-i', str(transition_video),
            '-filter_complex',
            # Part 1: Video1 before overlap
            f'[0:v]trim=0:{v1_dur - overlap_v1},setpts=PTS-STARTPTS[v1_before];'
            # Part 2: Last overlap_v1 of video1 with transition overlay
            f'[0:v]trim={v1_dur - overlap_v1}:{v1_dur},setpts=PTS-STARTPTS[v1_end];'
            f'[2:v]trim=0:{overlap_v1},setpts=PTS-STARTPTS,colorkey={greenscreen_color}:0.3:0.2[tr1];'
            f'[v1_end][tr1]overlay=0:0:shortest=1[overlap1];'
            # Part 3: First part of video2 with rest of transition
            f'[1:v]trim=0:{overlap_v2},setpts=PTS-STARTPTS,scale=1080:1920,setsar=1[v2_start];'
            f'[2:v]trim={overlap_v1}:{tr_dur},setpts=PTS-STARTPTS,colorkey={greenscreen_color}:0.3:0.2[tr2];'
            f'[v2_start][tr2]overlay=0:0:shortest=1[overlap2];'
            # Part 4: Rest of video2
            f'[1:v]trim={overlap_v2},setpts=PTS-STARTPTS,scale=1080:1920,setsar=1[v2_rest];'
            # Concat all video parts
            f'[v1_before][overlap1][overlap2][v2_rest]concat=n=4:v=1:a=0[vout];'
            # Audio: video1, transition audio, video2 rest
            f'[0:a]atrim=0:{v1_dur - overlap_v1},asetpts=PTS-STARTPTS[a1];'
            f'[2:a]asetpts=PTS-STARTPTS[a_tr];'
            f'[1:a]atrim={overlap_v2},asetpts=PTS-STARTPTS[a2];'
            f'[a1][a_tr][a2]concat=n=3:v=0:a=1[aout]',
            '-map', '[vout]',
            '-map', '[aout]',
            '-c:v', 'libx264', '-profile:v', 'high', '-pix_fmt', 'yuv420p',
            '-preset', 'medium', '-crf', '18', '-r', '60',
            '-c:a', 'aac', '-b:a', '192k',
            str(output_path)
        ]
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        output_dur = get_video_duration(output_path)
        print_success(f"Greenscreen merged: {output_path.name} ({output_dur:.2f}s)")
        return True
        
    except subprocess.CalledProcessError as e:
        print_error(f"Greenscreen merge failed: {e.stderr[:500] if e.stderr else str(e)}")
        return False
    except Exception as e:
        print_error(f"Greenscreen merge failed: {e}")
        return False


# ============================================================================
# MAIN PROCESSING FUNCTIONS
# ============================================================================

async def process_animal(animal_data, output_dir):
    """Process one animal: generate 2 videos with TTS"""
    
    task_name = animal_data.get("task", "unknown")
    animal_name = animal_data.get("animal", task_name.capitalize())
    clothes = animal_data.get("clothes", "")
    vehicle = animal_data.get("vehicle", "")
    
    # Print task header with animal info
    log.task_header(task_name, animal_name, clothes, vehicle)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get prompts
    image_prompt = animal_data["prompt"]
    dialog = animal_data.get("dialog")
    
    # Handle dialog format (string or array)
    if isinstance(dialog, str):
        dialog1 = dialog
        dialog2 = ""
    else:
        dialog1 = dialog[0] if len(dialog) > 0 else ""
        dialog2 = dialog[1] if len(dialog) > 1 else ""
    
    # Typography prompt
    edit_prompt = f"""Add bold sans-serif filled neon typography “{animal_name.upper()}”, center-aligned at the top, repeated vertically up to three rows with clean spacing and no overlap. Each row uses a different kid-friendly neon fill color (neon green, electric blue, neon pink/purple) with a soft glow only, no outline or stroke. Place the text behind the animal, partially occluded by the animal’s head for realistic depth, while keeping the animal and vehicle sharp, clear, and fully visible."""
    
    video1_prompt = f"""Create a continuous video with no background music and no animal sounds, Only include natural ambient sounds and vehicle engine sounds that match the scene. The background typography text "{animal_name.upper()}" fades out completely after 3 seconds using a smooth, modern transition.
The animal and the vehicle remain fully visible throughout the entire video with no cuts or scene changes, The vehicle moves in a straight path only, with no tracks, rails, curves, or guided paths."""
    
    # Video 2 prompt - UNIVERSAL
    video2_prompt = """No backsound effect. Make the animal talk by saying "Hello, Please vote for me by liking this video."
Keep all characters, clothing, accessories, props, and the background exactly the same.
Maintain perfect anatomy, no glitches, no floating parts.
Ensure the animal and all its actions stay fully visible in the frame at all times.
Use universal talking animation (mouth loop, subtle paw/hand movement), neutral/friendly expression."""
    
    # Step 1: Generate Image
    log.step("Create image")
    image_url = generate_image(image_prompt)
    if not image_url:
        log.fail(error="Cannot proceed without image", retry=False)
        return None
    
    original_image = output_dir / "01_original.jpg"
    if download_file(image_url, original_image):
        log.success(url=image_url, path=str(original_image))
    
    # OPENING: Different flow - no zoom out, use prompt-video, add text overlay
    if task_name == "opening":
        # Opening: skip zoom out, use image directly
        log.step("Zoom Out image")
        log.substep("Skipped (Opening task)", details={"reason": "Opening uses original image"})
        zoomed_url = image_url
        
        # Opening: skip typography
        log.step("Edit image")
        log.substep("Skipped (Opening task)", details={"reason": "No typography for opening"})
        edited_url = image_url
        
        # Opening: use prompt-video from JSON
        opening_video_prompt = animal_data.get("prompt-video", video1_prompt)
        log.info("Using", "prompt-video from JSON")
    else:
        # Non-opening: Zoom Out
        log.step("Zoom Out image")
        zoom_prompt = "Zoom Out"
        zoomed_url, zoomed_type = edit_image(zoom_prompt, image_url)
        if not zoomed_url:
            log.fail(error="Zoom Out failed, using original")
            zoomed_url = image_url
        else:
            zoomed_image = output_dir / "01b_zoomed.jpg"
            if download_file(zoomed_url, zoomed_image):
                log.success(url=zoomed_url, path=str(zoomed_image))
        
        # Non-opening: Add Typography
        log.step("Edit image (Typography)", index=1)
        edited_url, content_type = edit_image(edit_prompt, zoomed_url)
        if not edited_url:
            log.fail(error="Cannot proceed without edited image", retry=False)
            return None
        
        edited_image = output_dir / "02_edited.jpg"
        if download_file(edited_url, edited_image):
            log.success(url=edited_url, path=str(edited_image))
    
    # Step 3: Generate Video 1
    log.step("Image to Video", index=1)
    
    # Use opening_video_prompt for opening, video1_prompt for others
    if task_name == "opening":
        actual_video_prompt = opening_video_prompt
    else:
        actual_video_prompt = video1_prompt
    
    video1_id, video1_url = generate_video(actual_video_prompt, edited_url)
    if not video1_id:
        log.fail(error="Cannot proceed without video 1", retry=False)
        return None
    
    video1_path = output_dir / "03_video1.mp4"
    if download_file(video1_url, video1_path):
        log.success(url=video1_url, path=str(video1_path))
    
    # Step 3a: Upscale Video 1
    log.step("Video Upscale", index=1)
    video1_hd_url = upscale_video(video1_id)
    if not video1_hd_url:
        log.fail(error="Upscale failed, using original")
        video1_hd_path = video1_path
    else:
        video1_hd_path = output_dir / "03a_video1_hd.mp4"
        if download_file(video1_hd_url, video1_hd_path):
            log.success(url=video1_hd_url, path=str(video1_hd_path))
        else:
            video1_hd_path = video1_path
    
    # Step 3b: Convert to 60fps
    log.step("Convert to 1080p 60fps", index=1)
    video1_60fps = output_dir / "03b_video1_60fps.mp4"
    if convert_to_60fps(video1_hd_path, video1_60fps):
        log.success(path=str(video1_60fps))
    else:
        log.fail(error="Conversion failed")
        video1_60fps = video1_hd_path
    
    # Step 3c: Generate TTS and Apply Slowmo for Video 1
    if dialog1:
        print_header("Step 3c: Generate TTS for Video 1")
        tts1_path = output_dir / "03c_tts1.mp3"
        
        if await generate_tts(dialog1, VOICE_VIDEO1, tts1_path):
            # Get durations
            video1_dur = get_video_duration(video1_60fps)
            audio1_dur = get_audio_duration(tts1_path)
            
            print_info("Video duration", f"{video1_dur:.2f}s")
            print_info("Audio duration", f"{audio1_dur:.2f}s")
            
            # OPENING: No slowmo buffer (first video, no transition from previous)
            if task_name == "opening":
                print_info("Note", "Opening task - no slowmo buffer needed")
                
                # Just add audio normally (use original add_audio_to_video)
                print_header("Step 3d: Add TTS Audio to Video 1 (No Buffer)")
                video1_final = output_dir / "03d_video1_final.mp4"
                if not add_audio_to_video(video1_60fps, tts1_path, video1_final):
                    video1_final = video1_60fps
            else:
                # OTHER TASKS: Apply slowmo with buffer
                # If audio > video: slowmo = (audio - video) + buffer
                # If audio <= video: slowmo = buffer only
                if audio1_dur > video1_dur:
                    slowmo_extra = audio1_dur - video1_dur
                    target_duration = video1_dur + slowmo_extra + TRANSITION_BUFFER_DURATION
                    print_info("Strategy", f"Audio longer, need {slowmo_extra:.2f}s + {TRANSITION_BUFFER_DURATION}s buffer")
                else:
                    target_duration = video1_dur + TRANSITION_BUFFER_DURATION
                    print_info("Strategy", f"Audio fits, just adding {TRANSITION_BUFFER_DURATION}s buffer")
                
                # Step 3d: Apply slowmo
                print_header("Step 3d: Apply Slowmo to Video 1")
                video1_slowmo = output_dir / "03d_video1_slowmo.mp4"
                if not slowmo_video(video1_60fps, video1_slowmo, target_duration):
                    print_error("Slowmo failed, using original")
                    video1_slowmo = video1_60fps
                
                # Step 3e: Add audio to video (buffer at START)
                print_header("Step 3e: Add TTS Audio to Video 1 (With Buffer)")
                video1_final = output_dir / "03e_video1_final.mp4"
                
                slowmo_dur = get_video_duration(video1_slowmo)
                print_info("Total duration", f"{slowmo_dur:.2f}s")
                print_info("Buffer zone", f"0 - {TRANSITION_BUFFER_DURATION}s")
                
                # Add audio with buffer at START
                if not add_audio_to_video_with_buffer(video1_slowmo, tts1_path, video1_final, 
                                                       TRANSITION_BUFFER_DURATION):
                    video1_final = video1_slowmo
        else:
            video1_final = video1_60fps
    else:
        video1_final = video1_60fps

    
    # Check if this is opening task (only video 1)
    if task_name == "opening":
        print_info("Note", "Opening task - skipping video 2")
        
        # Add text overlay with dialog for opening (multi-line)
        video1_with_text = output_dir / "03f_video1_with_text.mp4"
        if add_text_overlay(video1_final, video1_with_text, dialog1):
            video1_final = video1_with_text
        
        print_success(f"✅ {task_name.upper()} completed!")
        return video1_final
    
    # Step 4: Edit Zoomed Image for Video 2
    log.step("Edit image", index=2)
    edit2_prompt = """Please change the background to look like it's in a different location, but the feel remains the same. Update the animal's expression and pose so it is laughing and confidently pointing toward the camera. Keep the animal, clothing, and vehicle consistent in color, size, proportions, art style (realistic), and patterns."""
    
    edited2_url, edited2_type = edit_image(edit2_prompt, zoomed_url)  # Use zoomed version
    if not edited2_url:
        log.fail(error="Cannot proceed without edited image for video 2", retry=False)
        return None
    
    edited2_image = output_dir / "04_edited_for_video2.jpg"
    if download_file(edited2_url, edited2_image):
        log.success(url=edited2_url, path=str(edited2_image))
    
    # Step 5: Generate Video 2
    print_header("Step 5: Generate Video 2")
    video2_id, video2_url = generate_video(video2_prompt, edited2_url)
    if not video2_id:
        print_error("Cannot proceed without video 2")
        return None
    
    video2_path = output_dir / "05_video2.mp4"
    if not download_file(video2_url, video2_path):
        return None
    
    # Step 5a: Upscale Video 2
    print_header("Step 5a: Upscale Video 2 to HD")
    video2_hd_url = upscale_video(video2_id)
    if not video2_hd_url:
        print_error("Upscale failed, using original")
        video2_hd_path = video2_path
    else:
        video2_hd_path = output_dir / "05a_video2_hd.mp4"
        if not download_file(video2_hd_url, video2_hd_path):
            video2_hd_path = video2_path
    
    # Step 5b: Convert to 60fps
    print_header("Step 5b: Convert Video 2 to 1080x1920 60fps")
    video2_60fps = output_dir / "05b_video2_60fps.mp4"
    if not convert_to_60fps(video2_hd_path, video2_60fps):
        print_error("Conversion failed")
        video2_60fps = video2_hd_path
    
    # Step 5c: Generate TTS and Apply Slowmo for Video 2
    VIDEO2_BUFFER = 1.0  # 1 second buffer at START (same as video1)
    
    if dialog2:
        print_header("Step 5c: Generate TTS for Video 2")
        tts2_path = output_dir / "05c_tts2.mp3"
        
        if await generate_tts(dialog2, VOICE_VIDEO2, tts2_path):
            # Get durations
            video2_dur = get_video_duration(video2_60fps)
            audio2_dur = get_audio_duration(tts2_path)
            
            print_info("Video duration", f"{video2_dur:.2f}s")
            print_info("Audio duration", f"{audio2_dur:.2f}s")
            
            # Calculate slowmo needed (buffer at START)
            if audio2_dur > video2_dur:
                slowmo_extra = audio2_dur - video2_dur
                target_duration = video2_dur + slowmo_extra + VIDEO2_BUFFER
                print_info("Strategy", f"Audio longer, need {slowmo_extra:.2f}s + {VIDEO2_BUFFER}s buffer")
            else:
                target_duration = video2_dur + VIDEO2_BUFFER
                print_info("Strategy", f"Audio fits, just adding {VIDEO2_BUFFER}s buffer at START")
            
            # Step 5d: Apply slowmo
            print_header("Step 5d: Apply Slowmo to Video 2")
            video2_slowmo = output_dir / "05d_video2_slowmo.mp4"
            if not slowmo_video(video2_60fps, video2_slowmo, target_duration):
                print_error("Slowmo failed, using original")
                video2_slowmo = video2_60fps
            
            # Step 5e: Add audio (buffer at START - same as video1)
            print_header("Step 5e: Add TTS Audio to Video 2 (Buffer at START)")
            video2_final = output_dir / "05e_video2_final.mp4"
            
            slowmo_dur = get_video_duration(video2_slowmo)
            print_info("Total duration", f"{slowmo_dur:.2f}s")
            print_info("Buffer zone", f"0 - {VIDEO2_BUFFER}s (START, empty)")
            
            # Add audio with buffer at START (same as video1)
            if not add_audio_to_video_with_buffer(video2_slowmo, tts2_path, video2_final, VIDEO2_BUFFER):
                video2_final = video2_slowmo
        else:
            video2_final = video2_60fps
    else:
        video2_final = video2_60fps
    
    # Step 5f: Add Trigger Overlay (like/subscribe/comment/share animation)
    if task_name in TRIGGER_OVERLAYS:
        log.step("Add Trigger Overlay", index=2)
        trigger_path = TRIGGER_OVERLAYS[task_name]
        
        if trigger_path.exists():
            video2_with_trigger = output_dir / "05f_video2_trigger.mp4"
            if add_trigger_overlay(video2_final, trigger_path, video2_with_trigger, 
                                   y_offset=TRIGGER_POSITION_Y_OFFSET):
                video2_final = video2_with_trigger
            else:
                log.fail(error="Trigger overlay failed, using video without trigger")
        else:
            log.fail(error=f"Trigger not found: {trigger_path}")
    
    # Step 6: Merge Video 1 and Video 2 (with swoosh sound)
    print_header("Step 6: Merge Videos (smoothright + swoosh)")
    merged_video = output_dir / "merged.mp4"
    if not merge_with_transition(video1_final, video2_final, merged_video, 
                                  transition="smoothright", duration=1.0, 
                                  swoosh_sound=SWOOSH_SOUND):
        return None
    
    print_success(f"✅ {task_name.upper()} completed!")
    return merged_video


async def main():
    """Main function to process all animals"""
    print("\n" + "═" * 60)
    print("  ADVANCED VIDEO GENERATOR WITH TTS")
    print("═" * 60)
    
    # Load naration.json
    with open("naration.json", "r") as f:
        animals = json.load(f)
    
    print(f"\nTotal animals to process: {len(animals)}")
    
    # Create base output directory
    BASE_OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Process each animal
    merged_videos = []
    for i, animal_data in enumerate(animals, 1):
        task_name = animal_data.get("task", f"animal_{i}")
        output_dir = BASE_OUTPUT_DIR / task_name
        
        print(f"\n[{i}/{len(animals)}] Processing {task_name}...")
        
        merged_video = await process_animal(animal_data, output_dir)
        if merged_video:
            merged_videos.append(merged_video)
        else:
            print_error(f"Failed to process {task_name}")
    
    # Final assembly: merge all videos with CUSTOM GREENSCREEN transitions
    if len(merged_videos) > 1:
        print("\n" + "═" * 60)
        print("  FINAL ASSEMBLY - Merging with Greenscreen Transitions")
        print("═" * 60)
        
        # Merge videos sequentially with custom greenscreen transition
        current_video = merged_videos[0]
        
        for i in range(1, len(merged_videos)):
            temp_output = BASE_OUTPUT_DIR / f"temp_merge_{i}.mp4"
            print_header(f"Merging video {i}/{len(merged_videos)-1} (Greenscreen)")
            
            # Use custom greenscreen transition for inter-animal merges
            if merge_with_greenscreen_transition(
                current_video, merged_videos[i], temp_output,
                transition_video=CUSTOM_TRANSITION_VIDEO,
                greenscreen_color=GREENSCREEN_COLOR,
                overlap_v1=GREENSCREEN_OVERLAP_V1
            ):
                current_video = temp_output
            else:
                print_error(f"Failed to merge video {i}")
                break

        
        # Rename final video
        final_video = BASE_OUTPUT_DIR / "final_complete_video.mp4"
        if current_video.exists():
            current_video.rename(final_video)
            
            # Add random backsound
            final_with_music = BASE_OUTPUT_DIR / "final_with_backsound.mp4"
            if add_backsound(final_video, final_with_music, volume=BACKSOUND_VOLUME):
                log.success(path=str(final_with_music))
            
            print("\n" + "═" * 60)
            print("  ✓ ALL PROCESSING COMPLETED!")
            print("═" * 60)
            print(f"\n🎉 Final video: {final_video.absolute()}")
            print(f"🎵 With music: {final_with_music.absolute()}\n")
    else:
        print_error("Not enough videos to merge")


if __name__ == "__main__":
    asyncio.run(main())
