Enhanced Finploy Sitemap Generator
A Python tool to efficiently discover and generate a sitemap for Finploy websites (finploy.com and finploy.co.uk), optimized to find more URLs quickly and accurately.

Features
Starts from base URLs and checks for existing sitemaps and robots.txt

Parses XML sitemaps and extracts URLs

Generates potential URLs based on common job-related patterns and locations

Validates URLs to avoid irrelevant or spam links

Crawls web pages to find additional URLs via links and embedded JavaScript

Limits crawling to a maximum number of URLs with controlled delay

Creates an XML sitemap file with URL priorities and change frequencies

Generates a detailed JSON report with crawl statistics and URL categorization

Logs progress and errors both on console and log file

Requirements
Python 3

requests library

beautifulsoup4 library

Install dependencies using:

bash
pip install requests beautifulsoup4
Usage
Run the script directly:

bash
python enhanced_finploy_sitemap_generator.py
The script will:

Check for existing sitemaps

Generate and test common job-related URLs

Crawl discovered URLs to find more links

Save an XML sitemap (enhanced_sitemap.xml)

Save a JSON report (enhanced_sitemap_report.json)

Log details in enhanced_sitemap.log

Output files
enhanced_sitemap.xml — Final sitemap with prioritized URLs

enhanced_sitemap_report.json — Summary of crawl stats and URL types

enhanced_sitemap.log — Crawl process logs

Customization
Modify BASE_URLS list in the main function to change target sites

Adjust delay and max_urls parameters when initializing EnhancedFinploySitemapGenerator for faster/slower crawling or larger/smaller sitemap

Notes
Designed specifically for Finploy job sites but can be adapted for similar domains

Includes basic error handling and graceful stop on keyboard interrupt
