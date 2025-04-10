import sys
import tempfile
import subprocess
from PIL import Image, ImageDraw, ImageFont


def add_text_to_image(img):
    draw = ImageDraw.Draw(img)

    # Text configurations
    main_text = "Dhuhr"
    sub_text = "13:34 - 15:30"
    main_font_size = 72
    sub_font_size = 48
    x_position = 50
    y_position = 645
    padding = 20

    # Load fonts with fallbacks
    try:
        main_font = ImageFont.truetype(
            "/System/Library/Fonts/HelveticaNeue.ttc", main_font_size, index=0
        )
    except IOError:
        try:
            main_font = ImageFont.truetype("/Library/Fonts/Arial.ttf", main_font_size)
        except IOError:
            main_font = ImageFont.load_default().font_variant(size=main_font_size)

    try:
        sub_font = ImageFont.truetype(
            "/System/Library/Fonts/HelveticaNeue.ttc", sub_font_size, index=0
        )
    except IOError:
        try:
            sub_font = ImageFont.truetype("/Library/Fonts/Arial.ttf", sub_font_size)
        except IOError:
            sub_font = ImageFont.load_default().font_variant(size=sub_font_size)

    # Text outline offsets
    outline_offsets = [
        (-1, -1),
        (-1, 0),
        (-1, 1),
        (0, -1),
        (0, 1),
        (1, -1),
        (1, 0),
        (1, 1),
    ]

    # Draw main text outline
    for dx, dy in outline_offsets:
        draw.text(
            (x_position + dx, y_position + dy), main_text, font=main_font, fill="black"
        )

    # Draw main text
    draw.text((x_position, y_position), main_text, font=main_font, fill="white")

    # Calculate subtext position
    main_bbox = draw.textbbox((x_position, y_position), main_text, font=main_font)
    sub_y = y_position + (main_bbox[3] - main_bbox[1]) + padding

    # Draw subtext outline
    for dx, dy in outline_offsets:
        draw.text((x_position + dx, sub_y + dy), sub_text, font=sub_font, fill="black")

    # Draw subtext
    draw.text((x_position, sub_y), sub_text, font=sub_font, fill="white")

    return img


def set_macos_wallpaper(file_path: str):
    escaped_path = file_path.replace('"', r"\"")
    applescript = f'''
    tell application "System Events"
        set picture of every desktop to "{escaped_path}"
    end tell
    '''
    subprocess.run(["osascript", "-e", applescript], check=True)


def main():
    if len(sys.argv) != 2:
        print("Usage: python set_wallpaper.py <image_path>")
        sys.exit(1)

    input_path = sys.argv[1]

    try:
        # Open and convert image to RGB if necessary
        with Image.open(input_path) as img:
            img = img.convert("RGB")
            modified_img = add_text_to_image(img)

            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
                temp_path = tmp_file.name
                modified_img.save(temp_path, "JPEG", quality=95)

            # Set wallpaper
            set_macos_wallpaper(temp_path)
            print("Wallpaper set successfully with prayer times.")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
