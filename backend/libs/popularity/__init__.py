"""
Popularity-Based Routing Library

This module implements popularity tracking and priority assignment
for topics in the distributed notification system.

Key Features:
- Track topic popularity (view counts, subscription counts)
- Assign priority levels based on popularity
- Integration with DynamoDB for persistent storage
- Support for popularity-based routing decisions

Benefits:
- High-priority notifications for popular topics
- Better resource allocation
- Improved user experience for trending events
"""

import time
import os
from typing import Dict, Optional, Tuple
from datetime import datetime

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    print("[Popularity] Warning: boto3 not available, using in-memory storage")


class PopularityTracker:
    """
    Tracks and manages topic popularity with DynamoDB integration.
    
    Popularity is based on:
    - Number of times event is published
    - Number of subscribers to the topic
    - Number of views/interactions (optional)
    """
    
    def __init__(self, 
                 table_name: Optional[str] = None,
                 use_dynamodb: bool = True,
                 thresholds: Optional[Dict[str, int]] = None):
        """
        Args:
            table_name: DynamoDB table name (default from env)
            use_dynamodb: Whether to use DynamoDB or in-memory storage
            thresholds: Priority thresholds {'low': 10, 'medium': 50, 'high': 100}
        """
        self.table_name = table_name or os.getenv('TOPIC_POPULARITY_TABLE', 'TopicPopularity')
        self.use_dynamodb = use_dynamodb and BOTO3_AVAILABLE
        
        # Priority thresholds
        self.thresholds = thresholds or {
            'low': 10,
            'medium': 50,
            'high': 100
        }
        
        # In-memory cache/fallback
        self.memory_store: Dict[str, Dict] = {}
        
        # Initialize DynamoDB client
        self.dynamodb = None
        self.table = None
        
        if self.use_dynamodb:
            try:
                self.dynamodb = boto3.resource(
                    'dynamodb',
                    region_name=os.getenv('AWS_REGION', 'us-east-1')
                )
                self.table = self.dynamodb.Table(self.table_name)
                print(f"[Popularity] Connected to DynamoDB table: {self.table_name}")
            except Exception as e:
                print(f"[Popularity] Failed to connect to DynamoDB: {e}")
                print("[Popularity] Falling back to in-memory storage")
                self.use_dynamodb = False
    
    def increment_topic(self, topic: str, amount: int = 1) -> int:
        """
        Increment the popularity count for a topic.
        
        This is called when:
        - An event is published to the topic
        - A user subscribes to the topic
        - A user views an event in the topic
        
        Args:
            topic: Topic name (e.g., 'hackathon.aiml')
            amount: Amount to increment by (default 1)
        
        Returns:
            New count value
        """
        if self.use_dynamodb:
            return self._increment_dynamodb(topic, amount)
        else:
            return self._increment_memory(topic, amount)
    
    def _increment_dynamodb(self, topic: str, amount: int) -> int:
        """Increment count in DynamoDB with atomic update"""
        try:
            response = self.table.update_item(
                Key={'topic': topic},
                UpdateExpression='ADD #count :amount SET last_updated = :timestamp',
                ExpressionAttributeNames={
                    '#count': 'count'
                },
                ExpressionAttributeValues={
                    ':amount': amount,
                    ':timestamp': int(time.time())
                },
                ReturnValues='UPDATED_NEW'
            )
            
            new_count = response['Attributes']['count']
            
            # Update memory cache
            self.memory_store[topic] = {
                'count': new_count,
                'last_updated': int(time.time())
            }
            
            return new_count
        
        except ClientError as e:
            print(f"[Popularity] DynamoDB error: {e}")
            # Fall back to memory
            return self._increment_memory(topic, amount)
    
    def _increment_memory(self, topic: str, amount: int) -> int:
        """Increment count in memory storage"""
        if topic not in self.memory_store:
            self.memory_store[topic] = {
                'count': 0,
                'last_updated': int(time.time())
            }
        
        self.memory_store[topic]['count'] += amount
        self.memory_store[topic]['last_updated'] = int(time.time())
        
        return self.memory_store[topic]['count']
    
    def get_count(self, topic: str) -> int:
        """
        Get current popularity count for a topic.
        
        Args:
            topic: Topic name
        
        Returns:
            Current count (0 if topic not found)
        """
        # Try memory cache first
        if topic in self.memory_store:
            return self.memory_store[topic]['count']
        
        # Try DynamoDB
        if self.use_dynamodb:
            try:
                response = self.table.get_item(Key={'topic': topic})
                if 'Item' in response:
                    count = response['Item']['count']
                    # Update cache
                    self.memory_store[topic] = {
                        'count': count,
                        'last_updated': response['Item'].get('last_updated', 0)
                    }
                    return count
            except ClientError as e:
                print(f"[Popularity] Error fetching from DynamoDB: {e}")
        
        return 0
    
    def get_priority(self, topic: str) -> str:
        """
        Get priority level for a topic based on popularity.
        
        Args:
            topic: Topic name
        
        Returns:
            Priority level: 'low', 'medium', or 'high'
        """
        count = self.get_count(topic)
        
        if count >= self.thresholds['high']:
            return 'high'
        elif count >= self.thresholds['medium']:
            return 'medium'
        elif count >= self.thresholds['low']:
            return 'low'
        else:
            return 'low'
    
    def get_topic_info(self, topic: str) -> Dict:
        """
        Get complete information about a topic's popularity.
        
        Args:
            topic: Topic name
        
        Returns:
            Dict with count, priority, last_updated
        """
        count = self.get_count(topic)
        priority = self.get_priority(topic)
        
        last_updated = 0
        if topic in self.memory_store:
            last_updated = self.memory_store[topic]['last_updated']
        
        return {
            'topic': topic,
            'count': count,
            'priority': priority,
            'last_updated': last_updated,
            'last_updated_readable': datetime.fromtimestamp(last_updated).isoformat() if last_updated else None
        }
    
    def get_top_topics(self, limit: int = 10) -> list:
        """
        Get the most popular topics.
        
        Args:
            limit: Maximum number of topics to return
        
        Returns:
            List of topic info dicts, sorted by count descending
        """
        # If using DynamoDB, we'd need a GSI on count for efficient querying
        # For now, use memory cache
        
        topics_with_counts = [
            {'topic': topic, 'count': data['count'], 'last_updated': data['last_updated']}
            for topic, data in self.memory_store.items()
        ]
        
        # Sort by count descending
        topics_with_counts.sort(key=lambda x: x['count'], reverse=True)
        
        return topics_with_counts[:limit]
    
    def bulk_save_to_dynamodb(self):
        """
        Save all in-memory popularity data to DynamoDB.
        
        This is typically called by the leader node periodically
        to persist aggregated popularity metrics.
        """
        if not self.use_dynamodb:
            print("[Popularity] DynamoDB not available, skipping bulk save")
            return
        
        saved_count = 0
        failed_count = 0
        
        for topic, data in self.memory_store.items():
            try:
                self.table.put_item(
                    Item={
                        'topic': topic,
                        'count': data['count'],
                        'last_updated': data['last_updated']
                    }
                )
                saved_count += 1
            except ClientError as e:
                print(f"[Popularity] Failed to save {topic}: {e}")
                failed_count += 1
        
        print(f"[Popularity] Bulk save complete: {saved_count} saved, {failed_count} failed")
    
    def reset_topic(self, topic: str):
        """Reset popularity count for a topic"""
        if topic in self.memory_store:
            del self.memory_store[topic]
        
        if self.use_dynamodb:
            try:
                self.table.delete_item(Key={'topic': topic})
            except ClientError as e:
                print(f"[Popularity] Error resetting topic: {e}")


# Global instance
_tracker_instance: Optional[PopularityTracker] = None


def get_tracker() -> PopularityTracker:
    """Get or create global PopularityTracker instance"""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = PopularityTracker()
    return _tracker_instance


def increment_topic(topic: str, amount: int = 1) -> int:
    """Convenience function to increment topic popularity"""
    return get_tracker().increment_topic(topic, amount)


def get_priority(topic: str) -> str:
    """Convenience function to get topic priority"""
    return get_tracker().get_priority(topic)


def get_count(topic: str) -> int:
    """Convenience function to get topic count"""
    return get_tracker().get_count(topic)


