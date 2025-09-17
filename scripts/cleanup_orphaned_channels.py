#!/usr/bin/env python3
"""
Script để cleanup các channel còn sót lại sau khi cuộc gọi kết thúc
"""

import requests
import json
import logging
from typing import List, Dict

# Cấu hình
ARI_HOST = "localhost"
ARI_PORT = 8088
ARI_USERNAME = "thanh"
ARI_PASSWORD = "1234"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChannelCleanup:
    def __init__(self):
        self.base_url = f"http://{ARI_HOST}:{ARI_PORT}/ari"
        self.auth = (ARI_USERNAME, ARI_PASSWORD)
    
    def get_all_channels(self) -> List[Dict]:
        """Lấy danh sách tất cả channels"""
        try:
            response = requests.get(f"{self.base_url}/channels", auth=self.auth)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting channels: {str(e)}")
            return []
    
    def get_all_bridges(self) -> List[Dict]:
        """Lấy danh sách tất cả bridges"""
        try:
            response = requests.get(f"{self.base_url}/bridges", auth=self.auth)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting bridges: {str(e)}")
            return []
    
    def hangup_channel(self, channel_id: str) -> bool:
        """Cúp máy channel"""
        try:
            response = requests.delete(f"{self.base_url}/channels/{channel_id}", auth=self.auth)
            if response.status_code == 204:
                logger.info(f"Successfully hung up channel {channel_id}")
                return True
            else:
                logger.warning(f"Failed to hangup channel {channel_id}: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error hanging up channel {channel_id}: {str(e)}")
            return False
    
    def destroy_bridge(self, bridge_id: str) -> bool:
        """Destroy bridge"""
        try:
            response = requests.delete(f"{self.base_url}/bridges/{bridge_id}", auth=self.auth)
            if response.status_code == 204:
                logger.info(f"Successfully destroyed bridge {bridge_id}")
                return True
            else:
                logger.warning(f"Failed to destroy bridge {bridge_id}: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error destroying bridge {bridge_id}: {str(e)}")
            return False
    
    def cleanup_orphaned_channels(self):
        """Cleanup các channel còn sót lại"""
        logger.info("Starting cleanup of orphaned channels...")
        
        # Lấy danh sách channels
        channels = self.get_all_channels()
        logger.info(f"Found {len(channels)} channels")
        
        # Lấy danh sách bridges
        bridges = self.get_all_bridges()
        logger.info(f"Found {len(bridges)} bridges")
        
        # Cleanup empty bridges trước
        for bridge in bridges:
            bridge_id = bridge.get("id")
            bridge_channels = bridge.get("channels", [])
            
            if len(bridge_channels) == 0:
                logger.info(f"Found empty bridge {bridge_id}, destroying...")
                self.destroy_bridge(bridge_id)
        
        # Cleanup orphaned channels
        for channel in channels:
            channel_id = channel.get("id")
            channel_state = channel.get("state")
            channel_name = channel.get("name", "")
            
            # Chỉ cleanup channels trong state "Up" và có tên chứa "UnicastRTP"
            if channel_state == "Up" and "UnicastRTP" in channel_name:
                logger.info(f"Found orphaned channel {channel_id} ({channel_name}), hanging up...")
                self.hangup_channel(channel_id)
        
        logger.info("Cleanup completed!")
    
    def show_status(self):
        """Hiển thị trạng thái hiện tại"""
        logger.info("Current status:")
        
        channels = self.get_all_channels()
        bridges = self.get_all_bridges()
        
        logger.info(f"Active channels: {len(channels)}")
        for channel in channels:
            channel_id = channel.get("id")
            channel_state = channel.get("state")
            channel_name = channel.get("name", "")
            logger.info(f"  - {channel_id}: {channel_state} ({channel_name})")
        
        logger.info(f"Active bridges: {len(bridges)}")
        for bridge in bridges:
            bridge_id = bridge.get("id")
            bridge_channels = bridge.get("channels", [])
            logger.info(f"  - {bridge_id}: {len(bridge_channels)} channels")

def main():
    cleanup = ChannelCleanup()
    
    print("🔍 Channel Cleanup Tool")
    print("1. Show current status")
    print("2. Cleanup orphaned channels")
    print("3. Exit")
    
    while True:
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            cleanup.show_status()
        elif choice == "2":
            confirm = input("Are you sure you want to cleanup orphaned channels? (y/N): ").strip().lower()
            if confirm == "y":
                cleanup.cleanup_orphaned_channels()
            else:
                print("Cleanup cancelled.")
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()
