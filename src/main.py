from dataclasses import dataclass
import datetime
import glob
import sys
import tempfile
import subprocess
from PIL import Image, ImageDraw, ImageFont
import requests
from pydantic import ValidationError, validate_call
from pydantic import BaseModel, Field
from typing import Annotated
# from AppKit import NSScreen


def get_screen_info():
    """Get actual screen dimensions accounting for Retina scaling"""
    # screen = NSScreen.mainScreen()
    # frame = screen.frame()
    # scale_factor = screen.backingScaleFactor()
    # return (int(frame.size.width * scale_factor),
    #         int(frame.size.height * scale_factor))
    return (2560, 1664)


def adapt_image(image: Image.Image, target_width: int, target_height: int):
    """Crop and resize image to match screen dimensions"""
    target_aspect = target_width / target_height
    img_width, img_height = image.size

    # Calculate crop dimensions
    if (img_width / img_height) > target_aspect:
        new_height = img_height
        new_width = int(target_aspect * new_height)
        x_offset = (img_width - new_width) // 2
        crop_box = (x_offset, 0, x_offset + new_width, new_height)
    else:
        new_width = img_width
        new_height = int(new_width / target_aspect)
        y_offset = (img_height - new_height) // 2
        crop_box = (0, y_offset, new_width, y_offset + new_height)

    return image.crop(crop_box).resize((target_width, target_height), Image.LANCZOS)


def add_watermark(
    main_text: str,
    sub_text: str,
    image: Image.Image,
    screen_width: int,
    screen_height: int,
):
    """Add text overlay with dynamic sizing"""
    draw = ImageDraw.Draw(image)

    # Dynamic sizing based on screen height
    # main_size = max(36, screen_height // 20)  # Minimum 36px
    # sub_size = max(24, screen_height // 30)  # Minimum 24px
    # margin = screen_height // 50

    main_size = 120
    sub_size = 40

    # Text positioning with safe margins
    text_x = screen_width * 0.05
    text_y = screen_height * 0.1

    # Font loading with multiple fallbacks
    fonts = [
        "/System/Library/Fonts/SanFrancisco.ttf",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/HelveticaNeue.ttc",
    ]

    try:
        main_font = ImageFont.truetype(fonts[0], main_size)
    except IOError:
        main_font = ImageFont.load_default().font_variant(size=main_size)

    try:
        sub_font = ImageFont.truetype(fonts[0], sub_size)
    except IOError:
        sub_font = ImageFont.load_default().font_variant(size=sub_size)

    # Main text
    # for dx, dy in outline_offsets:
    #     draw.text((text_x + dx, text_y + dy), "Dhuhr", font=main_font, fill="black")
    draw.text(
        (text_x, text_y),
        main_text,
        font=main_font,
        fill="white",
        stroke_fill="black",
        stroke_width=5,
    )

    # Subtext positioning
    _, _, _, main_text_bottom = draw.textbbox(
        (text_x, text_y), main_text, font=main_font
    )
    # sub_text_y = main_text_bottom + margin // 2
    sub_text_y = main_text_bottom + 10

    draw.text(
        (text_x, sub_text_y),
        sub_text,
        font=sub_font,
        fill="white",
        stroke_fill="black",
        stroke_width=3,
    )

    return image


def set_wallpaper(file_path: str):
    """Set wallpaper using macOS system commands"""
    _ = subprocess.run(
        [
            "osascript",
            "-e",
            f'tell application "System Events" to set picture of every desktop to "{file_path}"',
        ],
        check=True,
    )


# @dataclass


class salah_times(BaseModel):
    fajr: datetime.datetime
    dhuhr: datetime.datetime
    asr: datetime.datetime
    maghrib: datetime.datetime
    isha: datetime.datetime

    # Also add to it
    sunrise: datetime.datetime
    fajr_nextday: datetime.datetime


def salah_timings_greenlane():
    link = f"https://api.masjidbox.com/1.0/masjidbox/landing/athany/green-lane-masjid-1666108368685?get=at&days=2&begin={datetime.datetime.now().strftime('%Y-%m-%d')[:-3]}T00:00:00.000%2B01:00"
    value = requests.get(
        link,
        headers={
            "ApiKey": "JejYcMS7hsOsZTPDk2ZhKOAlW9IyQ6Px",
            "Referer": "https://masjidbox.com/",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        },
    ).json()

    return salah_times(
        fajr=value["timetable"][0]["fajr"],
        sunrise=value["timetable"][0]["sunrise"],
        dhuhr=value["timetable"][0]["dhuhr"],
        asr=value["timetable"][0]["asr"],
        maghrib=value["timetable"][0]["maghrib"],
        isha=value["timetable"][0]["isha"],
        fajr_nextday=value["timetable"][1]["fajr"],
    )


# @validate_call
# def wallpaper_for_time(time: datetime.datetime):
def wallpaper_for_time(salah: salah_times):
    wallpapers = glob.glob("./Images/*jpg")[1:]
    current = datetime.datetime.now().second % len(wallpapers)

    current_time = datetime.datetime.now()

    if salah.fajr <= current_time < salah.sunrise:
        return ("./Images/Big Sur Beach 2-3.jpg", "Fajr")
    elif salah.sunrise <= current_time < salah.dhuhr:
        return "./Images/Big Sur Beach 2-4.jpg", "Duha"
    elif salah.dhuhr <= current_time < salah.asr:
        return "./Images/Big Sur Beach 2-5.jpg", "Dhuhr"
    elif salah.asr <= current_time < salah.maghrib:
        return "./Images/Big Sur Beach 2-6.jpg", "Asr"
    elif salah.maghrib <= current_time < salah.isha:
        return "./Images/Big Sur Beach 2-7.jpg", "Maghrib"
    elif salah.isha <= current_time or current_time <= salah.fajr:
        ...
    else:
        raise Exception("This time-branch should be impossible")

    return wallpapers[current]


def main():
    # if len(sys.argv) != 2:
    #     print("Usage: python wallpaper_setter.py <image-path>")
    #     sys.exit(1)

    screen_width, screen_height = get_screen_info()
    # current_wallpaper = sys.argv[1]
    current_wallpaper = wallpaper_for_time()

    print(salah_timings_greenlane())

    try:
        with Image.open(current_wallpaper) as img:
            processed = adapt_image(img, screen_width, screen_height)
            watermarked = add_watermark(
                "Dhuhr", "its timings", processed, screen_width, screen_height
            )

            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                watermarked.save(tmp.name, "JPEG", quality=90)
                set_wallpaper(tmp.name)

        print("Wallpaper successfully updated with visible text!")

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
