"""
Publisher-Side Filtering Library

This module implements publisher-side filtering to reduce unnecessary
message processing and network traffic in the pub/sub system.

Key Benefits:
- Reduced network bandwidth (don't send to uninterested subscribers)
- Lower processing overhead in notification dispatcher
- More efficient use of RabbitMQ queues
- Better scalability

Filtering Criteria:
- Topic matching (exact or wildcard)
- Location-based filtering
- Experience level (internship, entry, senior, etc.)
- Event type (hackathon, job, workshop, etc.)
- Custom user preferences
"""

from typing import List, Dict, Optional, Set
import re


class EventFilter:
    """Filter events based on subscriber preferences"""
    
    @staticmethod
    def matches_topic(event_topic: str, subscription_topic: str) -> bool:
        """
        Check if event topic matches subscription topic pattern.
        
        Supports wildcards:
        - '*' matches any single level
        - '#' matches zero or more levels
        
        Examples:
        - 'hackathon.aiml' matches 'hackathon.aiml' (exact)
        - 'hackathon.*' matches 'hackathon.aiml', 'hackathon.web' (single level)
        - 'hackathon.#' matches 'hackathon.aiml.beginner' (multi-level)
        
        Args:
            event_topic: Topic of the event (e.g., 'jobs.internship.swe')
            subscription_topic: User's subscription pattern
            
        Returns:
            True if topics match
        """
        # Exact match
        if event_topic == subscription_topic:
            return True
        
        # Convert topic pattern to regex
        # Replace '.' with '\.' for literal dot
        # Replace '*' with '[^.]+' (one or more non-dot chars)
        # Replace '#' with '.*' (zero or more of any char)
        pattern = subscription_topic
        pattern = pattern.replace('.', r'\.')
        pattern = pattern.replace('*', r'[^.]+')
        pattern = pattern.replace('#', r'.*')
        pattern = f'^{pattern}$'
        
        try:
            return bool(re.match(pattern, event_topic))
        except re.error:
            # Invalid pattern, fall back to exact match
            return event_topic == subscription_topic
    
    @staticmethod
    def matches_location(event_location: Optional[str], 
                        preferred_locations: Optional[List[str]]) -> bool:
        """
        Check if event location matches user's preferred locations.
        
        Args:
            event_location: Location of the event
            preferred_locations: User's preferred locations (None = any)
            
        Returns:
            True if location matches or no preference set
        """
        if not preferred_locations:
            return True  # No location preference
        
        if not event_location:
            return False  # Event has no location but user has preference
        
        # Case-insensitive matching
        event_loc_lower = event_location.lower()
        
        for preferred in preferred_locations:
            if preferred.lower() in event_loc_lower or event_loc_lower in preferred.lower():
                return True
        
        return False
    
    @staticmethod
    def matches_level(event_level: Optional[str], 
                     preferred_levels: Optional[List[str]]) -> bool:
        """
        Check if event level matches user's preferred levels.
        
        Levels: 'internship', 'entry', 'mid', 'senior', 'beginner', 'intermediate', 'advanced'
        
        Args:
            event_level: Level/difficulty of the event
            preferred_levels: User's preferred levels (None = any)
            
        Returns:
            True if level matches or no preference set
        """
        if not preferred_levels:
            return True  # No level preference
        
        if not event_level:
            return True  # Event has no level, include it
        
        # Case-insensitive matching
        event_level_lower = event_level.lower()
        preferred_levels_lower = [l.lower() for l in preferred_levels]
        
        return event_level_lower in preferred_levels_lower
    
    @staticmethod
    def matches_filters(event: Dict, subscription_filters: Optional[Dict]) -> bool:
        """
        Check if event matches all subscription filters.
        
        Args:
            event: Event data dictionary
            subscription_filters: User's filter preferences
            
        Returns:
            True if all filters match
        """
        if not subscription_filters:
            return True  # No filters, all events match
        
        # Location filter
        if 'locations' in subscription_filters:
            event_location = event.get('location')
            preferred_locations = subscription_filters['locations']
            if not EventFilter.matches_location(event_location, preferred_locations):
                return False
        
        # Level filter
        if 'levels' in subscription_filters:
            event_level = event.get('level')
            preferred_levels = subscription_filters['levels']
            if not EventFilter.matches_level(event_level, preferred_levels):
                return False
        
        # Custom field filters
        if 'custom' in subscription_filters:
            for key, expected_values in subscription_filters['custom'].items():
                event_value = event.get(key)
                if event_value not in expected_values:
                    return False
        
        return True


def get_subscribers_for_event(event: Dict, 
                              subscriptions: List[Dict]) -> List[Dict]:
    """
    Filter subscriptions to find which users should receive this event.
    
    This implements PUBLISHER-SIDE FILTERING - a key distributed systems
    optimization that reduces unnecessary message processing.
    
    Args:
        event: Event data with keys: topic, location, level, etc.
        subscriptions: List of subscription dicts with:
            - user_id
            - topic (with possible wildcards)
            - channels (list: ['app', 'email', 'sms'])
            - filters (optional dict with location/level preferences)
    
    Returns:
        List of matching subscriptions (user_id + channels)
    """
    matching_subscribers = []
    event_topic = event.get('topic', '')
    
    for sub in subscriptions:
        sub_topic = sub.get('topic', '')
        
        # Check topic match
        if not EventFilter.matches_topic(event_topic, sub_topic):
            continue
        
        # Check additional filters
        sub_filters = sub.get('filters')
        if not EventFilter.matches_filters(event, sub_filters):
            continue
        
        # This subscription matches
        matching_subscribers.append({
            'user_id': sub['user_id'],
            'channels': sub.get('channels', ['app']),
            'subscription_topic': sub_topic
        })
    
    return matching_subscribers


def build_notification_payload(event: Dict, 
                               subscribers: List[Dict],
                               priority: str = "medium") -> Dict:
    """
    Build a notification message payload for RabbitMQ.
    
    Args:
        event: Event data
        subscribers: List of matching subscribers (from get_subscribers_for_event)
        priority: Priority level ('low', 'medium', 'high')
    
    Returns:
        Dictionary ready to publish to RabbitMQ
    """
    # Extract subscriber IDs and aggregate channels
    subscriber_ids = [s['user_id'] for s in subscribers]
    
    # Collect all unique channels requested
    all_channels = set()
    for s in subscribers:
        all_channels.update(s.get('channels', []))
    
    payload = {
        'event_id': event.get('event_id'),
        'topic': event.get('topic'),
        'title': event.get('title'),
        'description': event.get('description', ''),
        'start_time': event.get('start_time'),
        'location': event.get('location'),
        'media_url': event.get('media_url'),
        'subscriber_ids': subscriber_ids,
        'channels': list(all_channels),
        'priority': priority,
        'timestamp': event.get('timestamp'),
        'organizer_id': event.get('organizer_id')
    }
    
    return payload


def aggregate_subscriptions_by_topic(subscriptions: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Group subscriptions by topic for efficient lookup.
    
    Args:
        subscriptions: List of all subscriptions
    
    Returns:
        Dictionary mapping topic -> list of subscriptions
    """
    topic_map: Dict[str, List[Dict]] = {}
    
    for sub in subscriptions:
        topic = sub.get('topic', '')
        if topic not in topic_map:
            topic_map[topic] = []
        topic_map[topic].append(sub)
    
    return topic_map


def get_relevant_subscriptions(event_topic: str, 
                               topic_subscription_map: Dict[str, List[Dict]]) -> List[Dict]:
    """
    Get all subscriptions that might match an event topic.
    
    Handles wildcard subscriptions efficiently.
    
    Args:
        event_topic: Topic of the event
        topic_subscription_map: Pre-aggregated topic -> subscriptions map
    
    Returns:
        List of potentially matching subscriptions
    """
    relevant_subs = []
    
    # Check exact match
    if event_topic in topic_subscription_map:
        relevant_subs.extend(topic_subscription_map[event_topic])
    
    # Check wildcard subscriptions
    event_parts = event_topic.split('.')
    
    for sub_topic, subs in topic_subscription_map.items():
        if '*' in sub_topic or '#' in sub_topic:
            # This is a wildcard subscription, check all
            for sub in subs:
                if EventFilter.matches_topic(event_topic, sub_topic):
                    relevant_subs.append(sub)
    
    return relevant_subs


