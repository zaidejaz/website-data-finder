import requests
from bs4 import BeautifulSoup
import re
import logging
from colorlog import ColoredFormatter

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Setup color formatter
formatter = ColoredFormatter(
    "%(log_color)s[%(levelname)s] %(message)s",
    log_colors={
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "red,bg_white",
    },
)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)

def get_website_data(url):
    """
    This function scrapes a website and retrieves data as specified by the client.

    Args:
        url: The URL of the website to be scraped.

    Returns:
        A dictionary containing the extracted data:
            - owner_name: Extracted owner name (if found)
            - owner_emails: List of extracted owner email addresses (if found)
            - phone_numbers: List of extracted phone numbers (if found)
            - social_media_links: Dictionary of social media platform links (if found)
    """

    data = {
        "owner_name": "",
        "owner_emails": [],
        "phone_numbers": [],
        "social_media_links": {}
    }

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            logger.error(f"Failed to fetch the website: {url} with status code {response.status_code}")
            return data

        soup = BeautifulSoup(response.content, "html.parser")

        # Search in header, footer, main page, about us page
        for section in [soup.find("header"), soup.find("footer"), soup.find("body"), soup.find("div", id="about-us")]:
            if section:
                data.update(extract_data_from_section(section))

        # Search in all site policies
        for url in find_urls(url):
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.content, "html.parser")
            data.update(extract_data_from_section(soup))

        # Check ads.txt
        ads_txt_url = f"{url}/ads.txt"
        ads_txt_response = requests.get(ads_txt_url, headers=headers)
        if ads_txt_response.status_code == 200:
            ads_data = extract_data_from_ads_txt(ads_txt_response.text)
            email = ads_data["owner_email"]
            name = ads_data["owner_name"]
            if email != "":
                data["owner_emails"].extend(email)

            if name != "":
                data["owner_name"] = name 

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching website: {url} - {e}")

    return data

def extract_data_from_section(soup):
    """
    Extracts data from a given BeautifulSoup section.

    Args:
        soup: The BeautifulSoup object representing the section to be scraped.

    Returns:
        A dictionary containing the extracted data:
            - owner_name: Extracted owner name (if found)
            - owner_emails: List of extracted owner email addresses (if found)
            - phone_numbers: List of extracted phone numbers (if found)
            - social_media_links: Dictionary of social media platform links (if found)
    """

    extracted_data = {
        "owner_name": "",
        "owner_emails": [],
        "phone_numbers": [],
        "social_media_links": {}
    }

    # More owner name patterns added here
    owner_name_patterns = [
        r"Owner Name: (.*)",
        r"Contact Name: (.*)",
        r"About the Owner: (.*)",
        r"Owner: (.*)",
        r"Name: (.*)",  # General name pattern
        r"Managed by: (.*)",
        r"Business Owner: (.*)",
        r"Company Owner: (.*)",
        r"CEO: (.*)",
        r"President: (.*)",
        r"Founder: (.*)"
    ]
    
    for pattern in owner_name_patterns:
        match = re.search(pattern, soup.text, re.IGNORECASE)
        if match:
            extracted_data["owner_name"] = match.group(1).strip()
            break

    # Extract email addresses
    email_regex = r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+"
    emails = re.findall(email_regex, soup.text)
    extracted_data["owner_emails"].extend(emails)

    # Extract phone numbers using an accurate regex pattern
    phone_regex = r"(\+?\d{1,3}[-.\s]?)?(\(?\d{1,4}\)?)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{4,10}"
    phone_numbers = re.findall(phone_regex, soup.text)
    extracted_data["phone_numbers"].extend([num[0] + num[1] for num in phone_numbers])

    # Extract social media links
    social_media_links = {}
    for link in soup.find_all("a", href=True):
        url = link["href"]
        if "facebook.com" in url:
            social_media_links["facebook"] = url
        elif "twitter.com" in url:
            social_media_links["twitter"] = url
        elif "linkedin.com" in url:
            social_media_links["linkedin"] = url
        elif "youtube.com" in url:
            social_media_links["youtube"] = url
        elif "twitch.tv" in url:
            social_media_links["twitch"] = url
        elif "reddit.com" in url:
            social_media_links["reddit"] = url
        elif "pinterest.com" in url:
            social_media_links["pinterest"] = url
        elif "instagram.com" in url:
            social_media_links["instagram"] = url
        elif "tiktok.com" in url:
            social_media_links["tiktok"] = url
        elif "discord.com" in url:
            social_media_links["discord"] = url

    extracted_data["social_media_links"] = social_media_links

    return extracted_data

def find_urls(url):
    """
    Finds URLs for common website policies.

    Args:
        url: The base URL of the website.

    Returns:
        A list of URLs for website policies.
    """

    # Define common paths for different sections
    common_paths = [
        "/privacy-policy",
        "/terms-of-service",
        "/terms-of-use",
        "/cookies-policy",
        "/contact",
        "/contact-us",
        "/about",
        "/about-us",
        "/legal",
        "/legal-notice",
        "/disclaimer",
        "/support",
        "/help",
        "/careers",
        "/faq",
        "/faq.htm",
        "/faq.html",
        "/faq.aspx",
        "/blog",
        "/blog.htm",
        "/blog.html",
        "/sitemap",
    ]
    
    # Construct full URLs
    common_urls = [f"{url}{path}" for path in common_paths]
    
    return common_urls

def extract_data_from_ads_txt(ads_txt):
    """
    Extracts owner information from ads.txt file.

    Args:
        ads_txt: The content of the ads.txt file.

    Returns:
        A dictionary containing the extracted data:
            - owner_name: Extracted owner name (if found)
    """

    extracted_data = {"owner_name": ""}
    for line in ads_txt.splitlines():
        if "domainowner=" in line:
            extracted_data["owner_name"] = line.split("=")[1].strip()
            break
        elif "contact=" in line:
            extracted_data["owner_email"]=line.split("=")[1].strip()
            break
    return extracted_data
