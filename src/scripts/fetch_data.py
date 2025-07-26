#!/usr/bin/env python3
"""
Complete YouTube Channel Data Fetcher and CSV Creator
This script fetches data from a YouTube channel and saves it to CSV format.
"""

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pandas as pd
import os
import logging
from datetime import datetime
import json
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('youtube_fetch.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class YouTubeToCSV:
    def __init__(self, api_key, channel_id, output_dir="../../data"):
        self.api_key = api_key
        self.channel_id = channel_id
        self.output_dir = output_dir
        self.youtube = None
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # File paths
        self.csv_path = os.path.join(output_dir, 'youtube_channel_data.csv')
        self.metadata_path = os.path.join(output_dir, 'fetch_metadata.json')
        self.log_path = os.path.join(output_dir, 'fetch_log.txt')
    
    def initialize_youtube_client(self):
        """Initialize YouTube API client"""
        try:
            self.youtube = build('youtube', 'v3', developerKey=self.api_key)
            logger.info("YouTube API client initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize YouTube client: {e}")
            return False
    
    def get_channel_info(self):
        """Get basic channel information"""
        try:
            response = self.youtube.channels().list(
                part='snippet,statistics,contentDetails',
                id=self.channel_id
            ).execute()
            
            if not response['items']:
                raise ValueError(f"Channel not found: {self.channel_id}")
            
            channel_data = response['items'][0]
            info = {
                'channel_id': self.channel_id,
                'channel_name': channel_data['snippet']['title'],
                'subscriber_count': int(channel_data['statistics'].get('subscriberCount', 0)),
                'video_count': int(channel_data['statistics'].get('videoCount', 0)),
                'view_count': int(channel_data['statistics'].get('viewCount', 0)),
                'uploads_playlist': channel_data['contentDetails']['relatedPlaylists']['uploads']
            }
            
            logger.info(f"Channel: {info['channel_name']}")
            logger.info(f"Videos: {info['video_count']}, Subscribers: {info['subscriber_count']:,}")
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting channel info: {e}")
            return None
    
    def fetch_all_videos(self, max_videos=None):
        """Fetch all videos from the channel"""
        try:
            # Get channel info first
            channel_info = self.get_channel_info()
            if not channel_info:
                return None
            
            playlist_id = channel_info['uploads_playlist']
            videos = []
            next_page_token = None
            processed_count = 0
            
            logger.info(f"Starting to fetch videos from playlist: {playlist_id}")
            
            while True:
                try:
                    # Get playlist items
                    pl_response = self.youtube.playlistItems().list(
                        part='snippet',
                        playlistId=playlist_id,
                        maxResults=50,
                        pageToken=next_page_token
                    ).execute()
                    
                    if not pl_response['items']:
                        break
                    
                    # Extract video IDs for batch processing
                    video_ids = []
                    video_snippets = {}
                    
                    for item in pl_response['items']:
                        video_id = item['snippet']['resourceId']['videoId']
                        video_ids.append(video_id)
                        video_snippets[video_id] = {
                            'title': item['snippet']['title'],
                            'upload_date': item['snippet']['publishedAt'],
                            'description': item['snippet'].get('description', '')[:500]  # First 500 chars
                        }
                    
                    # Batch fetch video statistics
                    stats_response = self.youtube.videos().list(
                        part='statistics,contentDetails',
                        id=','.join(video_ids)
                    ).execute()
                    
                    # Process each video
                    for video_data in stats_response['items']:
                        video_id = video_data['id']
                        snippet = video_snippets.get(video_id, {})
                        stats = video_data.get('statistics', {})
                        content_details = video_data.get('contentDetails', {})
                        
                        video_info = {
                            'VideoID': video_id,
                            'Title': snippet.get('title', 'N/A'),
                            'UploadDate': snippet.get('upload_date', ''),
                            'Description': snippet.get('description', ''),
                            'Duration': content_details.get('duration', ''),
                            'Views': int(stats.get('viewCount', 0)),
                            'Likes': int(stats.get('likeCount', 0)),
                            'Dislikes': int(stats.get('dislikeCount', 0)),
                            'Comments': int(stats.get('commentCount', 0)),
                            'URL': f'https://www.youtube.com/watch?v={video_id}'
                        }
                        
                        videos.append(video_info)
                        processed_count += 1
                        
                        if max_videos and processed_count >= max_videos:
                            logger.info(f"Reached maximum video limit: {max_videos}")
                            break
                    
                    logger.info(f"Processed {processed_count} videos...")
                    
                    # Check for next page
                    next_page_token = pl_response.get('nextPageToken')
                    if not next_page_token or (max_videos and processed_count >= max_videos):
                        break
                        
                except HttpError as e:
                    logger.error(f"HTTP error during video fetch: {e}")
                    if e.resp.status == 403:
                        logger.error("API quota exceeded or forbidden access")
                    break
                except Exception as e:
                    logger.error(f"Error processing videos: {e}")
                    break
            
            logger.info(f"Successfully fetched {len(videos)} videos")
            return videos, channel_info
            
        except Exception as e:
            logger.error(f"Error in fetch_all_videos: {e}")
            return None, None
    
    def save_to_csv(self, videos, channel_info):
        """Save video data to CSV file"""
        try:
            if not videos:
                logger.warning("No videos to save")
                return None
            
            # Create DataFrame
            df = pd.DataFrame(videos)
            
            # Data cleaning and formatting
            df['UploadDate'] = pd.to_datetime(df['UploadDate'])
            df = df.sort_values('UploadDate', ascending=False)
            
            # Save main CSV
            df.to_csv(self.csv_path, index=False, encoding='utf-8')
            
            # Create backup with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(self.output_dir, f'youtube_backup_{timestamp}.csv')
            df.to_csv(backup_path, index=False, encoding='utf-8')
            
            # Create metadata
            metadata = {
                'fetch_timestamp': datetime.now().isoformat(),
                'channel_info': channel_info,
                'data_summary': {
                    'total_videos': len(df),
                    'total_views': int(df['Views'].sum()),
                    'total_likes': int(df['Likes'].sum()),
                    'total_comments': int(df['Comments'].sum()),
                    'avg_views_per_video': float(df['Views'].mean()),
                    'date_range': {
                        'earliest': df['UploadDate'].min().isoformat(),
                        'latest': df['UploadDate'].max().isoformat()
                    }
                },
                'files': {
                    'main_csv': self.csv_path,
                    'backup_csv': backup_path
                }
            }
            
            # Save metadata
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # Print summary
            self._print_success_summary(df, metadata)
            
            return self.csv_path
            
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")
            return None
    
    def _print_success_summary(self, df, metadata):
        """Print success summary"""
        print(f"\n{'='*60}")
        print(f"🎉 YOUTUBE DATA SUCCESSFULLY SAVED TO CSV! 🎉")
        print(f"{'='*60}")
        print(f"📺 Channel: {metadata['channel_info']['channel_name']}")
        print(f"📁 Main CSV: {self.csv_path}")
        print(f"💾 Backup: {metadata['files']['backup_csv']}")
        print(f"📊 Videos saved: {metadata['data_summary']['total_videos']:,}")
        print(f"👀 Total views: {metadata['data_summary']['total_views']:,}")
        print(f"👍 Total likes: {metadata['data_summary']['total_likes']:,}")
        print(f"💬 Total comments: {metadata['data_summary']['total_comments']:,}")
        print(f"📈 Avg views/video: {metadata['data_summary']['avg_views_per_video']:,.0f}")
        print(f"📅 Date range: {df['UploadDate'].min().date()} to {df['UploadDate'].max().date()}")
        print(f"{'='*60}")
        print(f"✅ You can now open '{os.path.basename(self.csv_path)}' in Excel or any spreadsheet application!")
    
    def run(self, max_videos=None):
        """Main execution function"""
        logger.info("Starting YouTube to CSV conversion...")
        
        # Initialize client
        if not self.initialize_youtube_client():
            return False
        
        # Fetch videos
        videos, channel_info = self.fetch_all_videos(max_videos)
        if not videos:
            logger.error("No videos fetched")
            return False
        
        # Save to CSV
        csv_path = self.save_to_csv(videos, channel_info)
        if csv_path:
            logger.info(f"Process completed successfully! CSV saved to: {csv_path}")
            return True
        else:
            logger.error("Failed to save CSV")
            return False

def main():
    """Main function for direct execution"""
    # Configuration
    API_KEY = 'AIzaSyBsbfiGCkruyLNa_OnD0R7NtQpARxwBmmY'  # Replace with your API key
    CHANNEL_ID = 'UCX6OQ3DkcsbYNE6H8uQQuVA'  # Replace with target channel ID
    OUTPUT_DIR = './data'  # Output directory
    MAX_VIDEOS = None  # Set to limit number of videos (None for all)
    
    # Create converter instance and run
    converter = YouTubeToCSV(API_KEY, CHANNEL_ID, OUTPUT_DIR)
    success = converter.run(MAX_VIDEOS)
    
    if success:
        print("\n✅ Conversion completed successfully!")
        print(f"📁 Check the '{OUTPUT_DIR}' folder for your CSV file.")
    else:
        print("\n❌ Conversion failed. Check the logs for details.")

if __name__ == "__main__":
    main()