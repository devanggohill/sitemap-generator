#!/usr/bin/env python3
"""
Enhanced Finploy Sitemap Generator
Optimized to discover more URLs while maintaining speed
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs, unquote
import xml.etree.ElementTree as ET
from datetime import datetime
import time
import logging
import json
import re
from collections import deque

class EnhancedFinploySitemapGenerator:
    def __init__(self, base_urls, delay=0.5, max_urls=5000):
        self.base_urls = base_urls
        self.delay = delay
        self.max_urls = max_urls
        self.discovered_urls = set()
        self.crawled_urls = set()
        self.failed_urls = set()
        self.url_queue = deque()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('enhanced_sitemap.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Enhanced session with better headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        self.start_time = time.time()
        
        # Common job-related terms for URL generation
        self.job_keywords = [
            'software', 'developer', 'engineer', 'manager', 'analyst', 'consultant',
            'sales', 'marketing', 'finance', 'hr', 'admin', 'support', 'designer',
            'data', 'product', 'project', 'business', 'customer', 'technical'
        ]
        
        # Common locations 
        self.locations = [
            'mumbai', 'delhi', 'bangalore', 'hyderabad', 'chennai', 'pune', 
            'kolkata', 'ahmedabad', 'jaipur', 'lucknow', 'kanpur', 'nagpur',
            'indore', 'bhopal', 'visakhapatnam', 'patna', 'vadodara', 'ghaziabad',
            'london', 'manchester', 'birmingham', 'leeds', 'glasgow', 'liverpool',
            'bristol', 'sheffield', 'edinburgh', 'leicester'
        ]
        
    def check_existing_sitemaps(self):
        """Check for existing sitemaps and robots.txt"""
        sitemap_urls = []
        
        for base_url in self.base_urls:
            # Check common sitemap locations
            potential_sitemaps = [
                f"{base_url}/sitemap.xml",
                f"{base_url}/sitemap_index.xml",
                f"{base_url}/sitemaps.xml",
                f"{base_url}/sitemap/",
                f"{base_url}/robots.txt"
            ]
            
            for sitemap_url in potential_sitemaps:
                try:
                    response = self.session.get(sitemap_url, timeout=10)
                    if response.status_code == 200:
                        if sitemap_url.endswith('robots.txt'):
                            # Parse robots.txt for sitemap references
                            for line in response.text.split('\n'):
                                line = line.strip()
                                if line.lower().startswith('sitemap:'):
                                    sitemap_ref = line.split(':', 1)[1].strip()
                                    sitemap_urls.append(sitemap_ref)
                        else:
                            sitemap_urls.append(sitemap_url)
                            self.logger.info(f"Found existing sitemap: {sitemap_url}")
                except:
                    continue
        
        return sitemap_urls
    
    def parse_sitemap(self, sitemap_url):
        """Parse XML sitemap to extract URLs"""
        try:
            response = self.session.get(sitemap_url, timeout=15)
            response.raise_for_status()
            
            # Try to parse as XML
            try:
                root = ET.fromstring(response.content)
            except ET.ParseError:
                return []
            
            urls = []
            
            # Handle sitemap index files
            if 'sitemapindex' in root.tag.lower():
                for sitemap in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap'):
                    loc = sitemap.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                    if loc is not None and loc.text:
                        # Recursively parse sub-sitemaps
                        sub_urls = self.parse_sitemap(loc.text)
                        urls.extend(sub_urls)
            else:
                # Handle regular sitemap files
                for url_elem in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
                    loc = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                    if loc is not None and loc.text:
                        urls.append(loc.text)
            
            self.logger.info(f"Extracted {len(urls)} URLs from sitemap: {sitemap_url}")
            return urls
            
        except Exception as e:
            self.logger.error(f"Error parsing sitemap {sitemap_url}: {e}")
            return []
    
    def generate_potential_urls(self):
        """Generate potential URLs based on common patterns"""
        potential_urls = set()
        
        for base_url in self.base_urls:
            # Add common page patterns
            common_patterns = [
                '/jobs', '/jobs/', '/careers', '/careers/', '/vacancies', '/opportunities',
                '/companies', '/employers', '/locations', '/departments', '/categories',
                '/search', '/browse', '/find-jobs', '/job-search',
                '/about', '/contact', '/privacy', '/terms', '/help', '/faq'
            ]
            
            for pattern in common_patterns:
                potential_urls.add(f"{base_url}{pattern}")
            
            # Generate location-based job URLs
            for location in self.locations[:20]:  # Limit to top 20 locations
                potential_urls.add(f"{base_url}/jobs-in-{location}")
                potential_urls.add(f"{base_url}/jobs/{location}")
                potential_urls.add(f"{base_url}/careers-in-{location}")
            
            # Generate job category URLs
            for keyword in self.job_keywords[:15]:  # Limit to top 15 keywords
                potential_urls.add(f"{base_url}/{keyword}-jobs")
                potential_urls.add(f"{base_url}/jobs/{keyword}")
                potential_urls.add(f"{base_url}/{keyword}-careers")
            
            # Generate combined location + job type URLs
            for keyword in self.job_keywords[:5]:  # Top 5 keywords
                for location in self.locations[:5]:  # Top 5 locations
                    potential_urls.add(f"{base_url}/{keyword}-jobs-in-{location}")
        
        return potential_urls
    
    def is_valid_url(self, url):
        """Enhanced URL validation"""
        try:
            parsed = urlparse(url)
            
            # Basic validation
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Check domain
            base_domains = ['finploy.com', 'finploy.co.uk']
            if not any(domain in parsed.netloc for domain in base_domains):
                return False
            
            # Skip certain file types
            skip_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.css', '.js', 
                             '.ico', '.xml', '.txt', '.zip', '.doc', '.docx']
            if any(url.lower().endswith(ext) for ext in skip_extensions):
                return False
            
            # Skip URLs that are too long (likely generated)
            if len(url) > 300:
                return False
            
            # Skip obvious spam/bot URLs
            spam_indicators = ['wp-admin', 'wp-content', 'admin', 'login', 'register']
            if any(indicator in url.lower() for indicator in spam_indicators):
                return False
            
            return True
            
        except Exception:
            return False
    
    def extract_urls_comprehensive(self, url, soup):
        """Comprehensive URL extraction"""
        urls = set()
        
        # Extract all anchor links
        for link in soup.find_all('a', href=True):
            href = link['href'].strip()
            if href and not href.startswith(('#', 'mailto:', 'tel:', 'javascript:')):
                full_url = urljoin(url, href).split('#')[0]
                if self.is_valid_url(full_url):
                    urls.add(full_url)
        
        # Look for URLs in various attributes
        url_attributes = ['data-href', 'data-url', 'data-link', 'href']
        for attr in url_attributes:
            for elem in soup.find_all(attrs={attr: True}):
                href = elem[attr]
                if href and isinstance(href, str):
                    full_url = urljoin(url, href).split('#')[0]
                    if self.is_valid_url(full_url):
                        urls.add(full_url)
        
        # Enhanced JavaScript parsing
        for script in soup.find_all('script'):
            if script.string:
                script_content = script.string
                
                # Multiple patterns for URL extraction
                patterns = [
                    r'"((?:https?://)?[^"]*(?:job|career|company|location|department)[^"]*)"',
                    r"'((?:https?://)?[^']*(?:job|career|company|location|department)[^']*)'",
                    r'url:\s*["\'](/?[^"\']+)["\']',
                    r'href:\s*["\'](/?[^"\']+)["\']',
                    r'link:\s*["\'](/?[^"\']+)["\']',
                    r'path:\s*["\'](/?[^"\']+)["\']'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, script_content, re.IGNORECASE)
                    for match in matches[:10]:  # Limit matches per script
                        if match.startswith('//'):
                            continue
                        full_url = urljoin(url, match).split('#')[0]
                        if self.is_valid_url(full_url):
                            urls.add(full_url)
        
        return urls
    
    def crawl_page(self, url):
        """Enhanced page crawling"""
        try:
            self.logger.info(f"Crawling: {url}")
            
            response = self.session.get(url, timeout=15, allow_redirects=True)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                return False
            
            # Handle redirects
            if response.url != url and self.is_valid_url(response.url):
                if response.url not in self.discovered_urls:
                    self.discovered_urls.add(response.url)
                    self.url_queue.append(response.url)
            
            # Parse content
            soup = BeautifulSoup(response.content, 'html.parser')
            found_urls = self.extract_urls_comprehensive(url, soup)
            
            # Add new URLs to queue
            new_urls = found_urls - self.discovered_urls
            for new_url in new_urls:
                if len(self.discovered_urls) < self.max_urls:
                    self.url_queue.append(new_url)
                    self.discovered_urls.add(new_url)
            
            self.crawled_urls.add(url)
            self.logger.info(f"✓ Found {len(found_urls)} URLs, {len(new_urls)} new")
            
            return True
            
        except Exception as e:
            self.logger.error(f"✗ Failed to crawl {url}: {e}")
            self.failed_urls.add(url)
            return False
    
    def test_potential_urls(self, potential_urls):
        """Test potential URLs to see if they exist"""
        valid_urls = set()
        
        self.logger.info(f"Testing {len(potential_urls)} potential URLs...")
        
        for i, url in enumerate(potential_urls):
            if i % 50 == 0:  # Progress update
                print(f"\r🔍 Testing potential URLs: {i}/{len(potential_urls)}", end="")
            
            try:
                # Quick HEAD request to check if URL exists
                response = self.session.head(url, timeout=5, allow_redirects=True)
                if response.status_code in [200, 301, 302]:
                    valid_urls.add(url)
                    if len(valid_urls) >= 500:  # Limit valid URLs to test
                        break
            except:
                continue
            
            time.sleep(0.1)  # Small delay
        
        print(f"\r🔍 Found {len(valid_urls)} valid URLs from {len(potential_urls)} tested")
        return valid_urls
    
    def generate_enhanced_sitemap(self):
        """Enhanced sitemap generation"""
        self.logger.info("🚀 Starting Enhanced Finploy Sitemap Generation")
        
        # Step 1: Check existing sitemaps
        existing_sitemaps = self.check_existing_sitemaps()
        for sitemap_url in existing_sitemaps:
            sitemap_urls = self.parse_sitemap(sitemap_url)
            for sitemap_url in sitemap_urls:
                if self.is_valid_url(sitemap_url):
                    self.discovered_urls.add(sitemap_url)
                    self.url_queue.append(sitemap_url)
        
        # Step 2: Add base URLs
        for base_url in self.base_urls:
            self.discovered_urls.add(base_url)
            self.url_queue.append(base_url)
        
        # Step 3: Generate and test potential URLs
        potential_urls = self.generate_potential_urls()
        valid_urls = self.test_potential_urls(potential_urls)
        
        for url in valid_urls:
            if url not in self.discovered_urls:
                self.discovered_urls.add(url)
                self.url_queue.append(url)
        
        self.logger.info(f"Starting crawl with {len(self.discovered_urls)} seed URLs")
        
        # Step 4: Crawl pages
        crawled_count = 0
        while self.url_queue and crawled_count < self.max_urls:
            url = self.url_queue.popleft()
            
            if url in self.crawled_urls:
                continue
            
            if self.crawl_page(url):
                crawled_count += 1
            
            # Progress update
            if crawled_count % 50 == 0:
                elapsed = (time.time() - self.start_time) / 60
                print(f"\r🔄 Progress: {crawled_count} crawled, {len(self.discovered_urls)} total URLs, {elapsed:.1f}min", end="")
            
            time.sleep(self.delay)
        
        print()  # New line
        elapsed = (time.time() - self.start_time) / 60
        self.logger.info(f"🏁 Enhanced crawling complete in {elapsed:.1f} minutes")
        self.logger.info(f"📊 Final stats - Discovered: {len(self.discovered_urls)}, Crawled: {len(self.crawled_urls)}, Failed: {len(self.failed_urls)}")
        
        return self.discovered_urls
    
    def create_sitemap_xml(self, urls, filename='enhanced_sitemap.xml'):
        """Create comprehensive XML sitemap"""
        urlset = ET.Element('urlset')
        urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
        
        # Sort URLs by priority
        def get_url_priority(url):
            url_lower = url.lower()
            if any(x in url_lower for x in ['job', 'career', 'vacancy']):
                return 1
            elif url in self.base_urls:
                return 2
            elif any(x in url_lower for x in ['company', 'location', 'department']):
                return 3
            else:
                return 4
        
        sorted_urls = sorted(urls, key=get_url_priority)
        
        for url in sorted_urls:
            url_elem = ET.SubElement(urlset, 'url')
            
            loc_elem = ET.SubElement(url_elem, 'loc')
            loc_elem.text = url
            
            lastmod_elem = ET.SubElement(url_elem, 'lastmod')
            lastmod_elem.text = datetime.now().strftime('%Y-%m-%d')
            
            changefreq_elem = ET.SubElement(url_elem, 'changefreq')
            priority_elem = ET.SubElement(url_elem, 'priority')
            
            priority = get_url_priority(url)
            if priority == 1:  # Job pages
                changefreq_elem.text = 'daily'
                priority_elem.text = '0.9'
            elif priority == 2:  # Home pages
                changefreq_elem.text = 'weekly'
                priority_elem.text = '1.0'
            elif priority == 3:  # Category pages
                changefreq_elem.text = 'weekly'
                priority_elem.text = '0.7'
            else:  # Other pages
                changefreq_elem.text = 'monthly'
                priority_elem.text = '0.5'
        
        tree = ET.ElementTree(urlset)
        ET.indent(tree, space="  ", level=0)
        tree.write(filename, encoding='utf-8', xml_declaration=True)
        
        self.logger.info(f"💾 Enhanced sitemap saved: {filename} ({len(urls)} URLs)")
    
    def generate_report(self):
        """Generate comprehensive report"""
        elapsed = (time.time() - self.start_time) / 60
        
        # Categorize URLs
        categories = {
            'job_listings': 0,
            'company_pages': 0,
            'location_pages': 0,
            'department_pages': 0,
            'career_pages': 0,
            'other': 0
        }
        
        for url in self.discovered_urls:
            url_lower = url.lower()
            if any(x in url_lower for x in ['job', 'vacancy', 'opening']):
                categories['job_listings'] += 1
            elif any(x in url_lower for x in ['company', 'employer']):
                categories['company_pages'] += 1
            elif any(x in url_lower for x in ['location', 'city', 'jobs-in-']):
                categories['location_pages'] += 1
            elif any(x in url_lower for x in ['department', 'category']):
                categories['department_pages'] += 1
            elif any(x in url_lower for x in ['career', 'hiring']):
                categories['career_pages'] += 1
            else:
                categories['other'] += 1
        
        report = {
            'generation_time': datetime.now().isoformat(),
            'elapsed_minutes': round(elapsed, 1),
            'total_urls_discovered': len(self.discovered_urls),
            'total_urls_crawled': len(self.crawled_urls),
            'failed_urls': len(self.failed_urls),
            'success_rate': round((len(self.crawled_urls) / max(1, len(self.crawled_urls) + len(self.failed_urls)) * 100), 1),
            'url_categories': categories
        }
        
        with open('enhanced_sitemap_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        return report


def main():
    """Enhanced main execution"""
    BASE_URLS = [
        'https://www.finploy.com',
        'https://finploy.co.uk'
    ]
    
    print("🚀 Enhanced Finploy Sitemap Generator")
    print("🎯 Designed to discover maximum URLs efficiently")
    print("="*60)
    
    generator = EnhancedFinploySitemapGenerator(
        base_urls=BASE_URLS,
        delay=0.5,
        max_urls=3000
    )
    
    try:
        start_time = time.time()
        
        # Generate enhanced sitemap
        discovered_urls = generator.generate_enhanced_sitemap()
        
        # Create outputs
        generator.create_sitemap_xml(discovered_urls)
        report = generator.generate_report()
        
        elapsed = (time.time() - start_time) / 60
        
        print("\n" + "="*60)
        print("🎉 ENHANCED SITEMAP GENERATION COMPLETE!")
        print("="*60)
        print(f"⏱️  Total Time: {elapsed:.1f} minutes")
        print(f"📊 URLs Discovered: {report['total_urls_discovered']}")
        print(f"✅ URLs Crawled: {report['total_urls_crawled']}")
        print(f"❌ Failed: {report['failed_urls']}")
        print(f"📈 Success Rate: {report['success_rate']}%")
        
        print(f"\n📂 URL Categories:")
        for category, count in report['url_categories'].items():
            if count > 0:
                print(f"   {category.replace('_', ' ').title()}: {count}")
        
        print(f"\n💾 Files Generated:")
        print(f"   • enhanced_sitemap.xml ({report['total_urls_discovered']} URLs)")
        print(f"   • enhanced_sitemap_report.json")
        print(f"   • enhanced_sitemap.log")
        
        if report['total_urls_discovered'] > 500:
            print(f"\n✨ Successfully discovered {report['total_urls_discovered']} URLs - excellent coverage!")
        elif report['total_urls_discovered'] > 200:
            print(f"\n👍 Good coverage with {report['total_urls_discovered']} URLs discovered")
        else:
            print(f"\n💡 Discovered {report['total_urls_discovered']} URLs - may need manual review of site structure")
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Stopped by user - saving results...")
        if generator.discovered_urls:
            generator.create_sitemap_xml(generator.discovered_urls)
            generator.generate_report()
            print("✅ Partial results saved!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if generator.discovered_urls:
            generator.create_sitemap_xml(generator.discovered_urls)
            generator.generate_report()


if __name__ == "__main__":
    main()