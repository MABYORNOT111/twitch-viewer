import requests
import argparse
import json
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import sys

# Mobile proxy configuration
PROXY_URL = "http://pd37_mobi_rsn2po:cnjAtFrxrMNStvdKyOlT@proxy.insideproxy.net:8080"
PROXIES = {
    "http": PROXY_URL,
    "https": PROXY_URL
}

# Twitch API endpoints
TWITCH_API_BASE = "https://www.twitch.tv/api/v1"
TWITCH_GRAPHQL = "https://gql.twitch.tv/gql"

class TwitchViewer:
    def __init__(self, use_proxy=True):
        self.session = requests.Session()
        if use_proxy:
            self.session.proxies.update(PROXIES)
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
    
    def search_streamer(self, streamer_name: str) -> Optional[Dict]:
        """Search for a specific streamer and get their live status"""
        try:
            url = f"https://www.twitch.tv/{streamer_name}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                # Extract live status and viewer count from page
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Try to find viewer count in the page
                try:
                    data = self._extract_stream_data(response.text, streamer_name)
                    return data
                except:
                    return {
                        "name": streamer_name,
                        "status": "unknown",
                        "viewers": None
                    }
            else:
                return {
                    "name": streamer_name,
                    "status": "offline",
                    "viewers": 0
                }
        except Exception as e:
            print(f"Error searching for {streamer_name}: {e}")
            return None
    
    def _extract_stream_data(self, html_content: str, streamer_name: str) -> Dict:
        """Extract stream data from HTML"""
        try:
            # Look for live indicator and viewer count
            if "isLiveBroadcast" in html_content or "live" in html_content.lower():
                import re
                # Try to find viewer count pattern
                viewer_pattern = r'"viewers":(\d+)'
                match = re.search(viewer_pattern, html_content)
                viewers = int(match.group(1)) if match else 0
                
                return {
                    "name": streamer_name,
                    "status": "online",
                    "viewers": viewers
                }
            else:
                return {
                    "name": streamer_name,
                    "status": "offline",
                    "viewers": 0
                }
        except:
            return {
                "name": streamer_name,
                "status": "unknown",
                "viewers": None
            }
    
    def search_by_viewers(self, min_viewers: int, max_viewers: int) -> List[Dict]:
        """Find live streamers within a viewer count range"""
        print(f"Searching for streams with {min_viewers}-{max_viewers} viewers...")
        print("Note: This uses publicly available Twitch data")
        
        # Get directory/discovery page
        try:
            url = "https://www.twitch.tv/directory/all"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                streams = []
                
                # This is a simplified extraction - Twitch heavily uses JavaScript
                # In production, you might need Selenium or a dedicated API wrapper
                return self._extract_streams_from_directory(response.text, min_viewers, max_viewers)
            
            return []
        except Exception as e:
            print(f"Error searching by viewers: {e}")
            return []
    
    def _extract_streams_from_directory(self, html_content: str, min_v: int, max_v: int) -> List[Dict]:
        """Extract streams from directory page"""
        import re
        streams = []
        
        # Try to find stream data in the HTML
        viewer_pattern = r'"viewers":(\d+)'
        name_pattern = r'"displayName":"([^"]+)"'
        
        viewers = re.findall(viewer_pattern, html_content)
        names = re.findall(name_pattern, html_content)
        
        for i, (name, viewer_count) in enumerate(zip(names[:len(viewers)], viewers)):
            viewer_count = int(viewer_count)
            if min_v <= viewer_count <= max_v:
                streams.append({
                    "name": name,
                    "viewers": viewer_count,
                    "status": "online"
                })
        
        return streams[:10]  # Return top 10

def main():
    parser = argparse.ArgumentParser(description="Twitch Viewer Tool with Mobile Proxy")
    parser.add_argument("--streamer", type=str, help="Search for a specific streamer")
    parser.add_argument("--viewers", type=int, nargs=2, metavar=("MIN", "MAX"), 
                        help="Search for streamers with viewer count in range (min max)")
    
    args = parser.parse_args()
    
    viewer = TwitchViewer(use_proxy=True)
    
    if args.streamer:
        print(f"\n🔍 Searching for streamer: {args.streamer}")
        result = viewer.search_streamer(args.streamer)
        if result:
            print(f"\n✅ Results:")
            print(f"   Streamer: {result['name']}")
            print(f"   Status: {result['status'].upper()}")
            if result['viewers'] is not None:
                print(f"   Viewers: {result['viewers']}")
        else:
            print(f"❌ Could not find {args.streamer}")
    
    elif args.viewers:
        min_v, max_v = args.viewers
        print(f"\n🔍 Searching for streams with {min_v}-{max_v} viewers...")
        results = viewer.search_by_viewers(min_v, max_v)
        if results:
            print(f"\n✅ Found {len(results)} streams:")
            for stream in results:
                print(f"   • {stream['name']} - {stream['viewers']} viewers")
        else:
            print("❌ No streams found in that viewer range")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()