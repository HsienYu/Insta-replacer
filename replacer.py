from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import StaleElementReferenceException


import time
import asyncio
import random


# Define the session ID
SESSION_ID = "your_session_id_here"

# Initialize FirefoxOptions
# test on macOS only for RPi linux OS may need to load the geckodriver in the PATH
options = Options()
options.add_argument("--width=800")
options.add_argument("--height=1440")
driver = webdriver.Firefox(options=options)
driver.set_window_position(0, 0)
driver.get('https://www.instagram.com')

# wait for the page to load
time.sleep(2)


# login by session to avoid some login issues
# Set the session cookie
driver.add_cookie({
    "name": "sessionid",
    "value": SESSION_ID,
    "domain": ".instagram.com",
    "path": "/",
    "secure": True,
    "httpOnly": True
})

# Refresh the page to apply the session
driver.refresh()

# Now you should be logged in with the session ID
print("Logged in with session ID")

# Wait for the page to load
time.sleep(5)

# click "Not Now" buttons
# i think not neqssary to fo aync here


def click_not_now():
    try:
        # Click "Not Now" for saving login info
        not_store = driver.find_element(By.XPATH, '//button[text()="Not Now"]')
        not_store.click()
        print("Not Now Store")
        time.sleep(3)
    except Exception as e:
        print("No 'Not Now' for saving login info found:", e)

    # try:
    #     # Click "Not Now" for notifications
    #     not_notification = driver.find_element(By.CSS_SELECTOR, 'button._a9_1')
    #     not_notification.click()
    #     print("Not Now Notification")
    # except Exception as e:
    #     print("No 'Not Now' for notifications found:", e)


# Function to wait for all images and videos to load
async def preload_media():
    # Preload images
    images = driver.find_elements(By.CSS_SELECTOR, 'img')
    for img in images:
        try:
            driver.execute_script("""
                return new Promise((resolve) => {
                    if (arguments[0].complete) {
                        resolve();
                    } else {
                        arguments[0].addEventListener('load', resolve);
                        arguments[0].addEventListener('error', resolve);
                    }
                });
            """, img)
        except StaleElementReferenceException:
            print(
                "StaleElementReferenceException encountered for an image. Skipping this element.")

    # Preload videos
    videos = driver.find_elements(By.CSS_SELECTOR, 'video')
    for video in videos:
        try:
            driver.execute_script("""
                return new Promise((resolve) => {
                    if (arguments[0].readyState >= 3) {  // HAVE_FUTURE_DATA
                        resolve();
                    } else {
                        arguments[0].addEventListener('canplay', resolve);
                        arguments[0].addEventListener('error', resolve);
                    }
                });
            """, video)
        except StaleElementReferenceException:
            print(
                "StaleElementReferenceException encountered for a video. Skipping this element.")

    print("All images and videos preloaded")

# Function to disable images and videos


async def disable_media():
    # Disable images
    images = driver.find_elements(By.CSS_SELECTOR, 'img')
    for img in images:
        try:
            driver.execute_script("arguments[0].style.display = 'none';", img)
            # Find image's parent element and change background color to green
            driver.execute_script(
                "arguments[0].style.backgroundColor = '#0F0';", img.find_element(By.XPATH, '..'))
        except StaleElementReferenceException:
            print(
                "StaleElementReferenceException encountered for an image. Skipping this element.")

    # Disable videos
    videos = driver.find_elements(By.CSS_SELECTOR, 'video')
    for video in videos:
        try:
            driver.execute_script(
                "arguments[0].style.display = 'none';", video)
            # Find video's parent element and change background color to green
            driver.execute_script(
                "arguments[0].style.backgroundColor = '#0F0';", video.find_element(By.XPATH, '..'))
        except StaleElementReferenceException:
            print(
                "StaleElementReferenceException encountered for a video. Skipping this element.")

    print("All images and videos disabled")

# Scroll down


async def page_scrolling(timeout):
    scroll_pause_time = timeout
    screen_height = driver.execute_script("return window.screen.height;")
    i = 0.5
    previous_scroll_height = 0
    attempts = 0
    max_attempts = 5

    while True:
        await preload_media()
        await disable_media()
        driver.execute_script(
            "window.scrollTo(0, {screen_height}*{i});".format(screen_height=screen_height, i=i))
        i += 0.5
        time.sleep(scroll_pause_time)
        scroll_height = driver.execute_script(
            "return document.body.scrollHeight;")

        if scroll_height == previous_scroll_height:
            attempts += 1
            if attempts >= max_attempts:
                print("Reached the bottom of the page or no new content is loading.")
                break
        else:
            attempts = 0

        previous_scroll_height = scroll_height

        if (screen_height) * i > scroll_height:
            print("Scrolling down to the bottom of the page")
            break

    # Scroll back to the top
    while i > 0:
        i -= 0.5
        driver.execute_script(
            "window.scrollTo(0, {screen_height}*{i});".format(screen_height=screen_height, i=i))
        time.sleep(scroll_pause_time)
        if i <= 0:
            print("Scrolled back to the top of the page")
            break

# Main function


async def main():
    await asyncio.sleep(5)
    click_not_now()
    await preload_media()
    await disable_media()
    await asyncio.sleep(1)
    await page_scrolling(2)

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Script interrupted by user")
finally:
    driver.quit()
