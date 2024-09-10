from selenium.webdriver.firefox.service import Service
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException


import asyncio
from concurrent.futures import ThreadPoolExecutor


# Define the session ID
SESSION_ID = "{your SESSION_ID here}"

# Initialize FirefoxOptions
# test on macOS only for RPi linux OS may need to load the geckodriver in the PATH
options = Options()
options.add_argument("--width=800")
options.add_argument("--height=1440")
driver = webdriver.Firefox(options=options)
# load specific path for driver if needed
'''Specify the path to the geckodriver executable'''
# geckodriver_path = "/webdriver/geckodriver"
# service = Service(executable_path=geckodriver_path)
# driver = webdriver.Firefox(service=service, options=options)

# Set the window size and position
driver.set_window_position(0, 0)
driver.get('https://www.instagram.com')


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

# click "Not Now" buttons
# i think not neqssary to fo aync here


def click_not_now():
    try:
        # Click "Not Now" for saving login info
        not_store = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, '//button[text()="Not Now"]'))
        )
        not_store.click()
        print("Not Now Store")
    except TimeoutException:
        print("No 'Not Now' for saving login info found")


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
    pixels_per_step = screen_height // 2  # Scroll by half screen height per step
    previous_scroll_height = 0
    attempts = 0
    max_attempts = 5

    while True:
        await preload_media()
        await disable_media()
        driver.execute_script("window.scrollBy(0, {pixels_per_step});".format(
            pixels_per_step=pixels_per_step))
        await asyncio.sleep(scroll_pause_time)
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

        if driver.execute_script("return window.pageYOffset + window.innerHeight;") >= scroll_height:
            print("Scrolling down to the bottom of the page")
            break

    # Scroll back to the top
    while driver.execute_script("return window.pageYOffset;") > 0:
        driver.execute_script(
            "window.scrollBy(0, -{pixels_per_step});".format(pixels_per_step=pixels_per_step))
        await asyncio.sleep(scroll_pause_time)
        if driver.execute_script("return window.pageYOffset;") <= 0:
            print("Scrolled back to the top of the page")
            break


# Main function


async def main():
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        try:
            await asyncio.sleep(5)
            await loop.run_in_executor(executor, click_not_now)
            await preload_media()
            await disable_media()
            await asyncio.sleep(1)
            await page_scrolling(2)
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            driver.quit()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Script interrupted by user")
    finally:
        driver.quit()
