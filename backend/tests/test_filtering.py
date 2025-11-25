"""
Unit Tests for Publisher-Side Filtering

Tests the filtering logic including:
- Topic matching with wildcards
- Location filtering
- Level filtering
- Subscription filtering
"""

import unittest
from backend.libs.filtering import EventFilter, get_subscribers_for_event, build_notification_payload


class TestEventFilter(unittest.TestCase):
    """Test cases for Event Filtering"""
    
    def test_exact_topic_match(self):
        """Test exact topic matching"""
        self.assertTrue(EventFilter.matches_topic("hackathon.aiml", "hackathon.aiml"))
        self.assertFalse(EventFilter.matches_topic("hackathon.web", "hackathon.aiml"))
    
    def test_wildcard_single_level(self):
        """Test single-level wildcard (*) matching"""
        # * matches single level
        self.assertTrue(EventFilter.matches_topic("hackathon.aiml", "hackathon.*"))
        self.assertTrue(EventFilter.matches_topic("hackathon.web", "hackathon.*"))
        self.assertFalse(EventFilter.matches_topic("hackathon.aiml.advanced", "hackathon.*"))
    
    def test_wildcard_multi_level(self):
        """Test multi-level wildcard (#) matching"""
        # # matches zero or more levels
        self.assertTrue(EventFilter.matches_topic("hackathon.aiml", "hackathon.#"))
        self.assertTrue(EventFilter.matches_topic("hackathon.aiml.advanced", "hackathon.#"))
        self.assertTrue(EventFilter.matches_topic("hackathon", "hackathon.#"))
    
    def test_location_matching(self):
        """Test location filtering"""
        # No preference - should match
        self.assertTrue(EventFilter.matches_location("San Francisco", None))
        self.assertTrue(EventFilter.matches_location("San Francisco", []))
        
        # Exact match
        self.assertTrue(EventFilter.matches_location("San Francisco", ["San Francisco"]))
        
        # Partial match
        self.assertTrue(EventFilter.matches_location("San Francisco, CA", ["San Francisco"]))
        
        # No match
        self.assertFalse(EventFilter.matches_location("New York", ["San Francisco"]))
        
        # Event without location but user has preference
        self.assertFalse(EventFilter.matches_location(None, ["San Francisco"]))
    
    def test_level_matching(self):
        """Test level filtering"""
        # No preference - should match
        self.assertTrue(EventFilter.matches_level("beginner", None))
        self.assertTrue(EventFilter.matches_level("beginner", []))
        
        # Match
        self.assertTrue(EventFilter.matches_level("beginner", ["beginner", "intermediate"]))
        
        # No match
        self.assertFalse(EventFilter.matches_level("advanced", ["beginner"]))
        
        # Event without level - should match
        self.assertTrue(EventFilter.matches_level(None, ["beginner"]))
    
    def test_matches_filters_no_filters(self):
        """Test event matching with no filters"""
        event = {"title": "Test Event", "topic": "hackathon.aiml"}
        self.assertTrue(EventFilter.matches_filters(event, None))
        self.assertTrue(EventFilter.matches_filters(event, {}))
    
    def test_matches_filters_with_location(self):
        """Test event matching with location filter"""
        event = {
            "title": "Test Event",
            "location": "San Francisco, CA"
        }
        
        filters = {
            "locations": ["San Francisco", "Remote"]
        }
        
        self.assertTrue(EventFilter.matches_filters(event, filters))
        
        # No match
        filters_no_match = {
            "locations": ["New York"]
        }
        self.assertFalse(EventFilter.matches_filters(event, filters_no_match))
    
    def test_matches_filters_with_level(self):
        """Test event matching with level filter"""
        event = {
            "title": "Test Event",
            "level": "intermediate"
        }
        
        filters = {
            "levels": ["beginner", "intermediate"]
        }
        
        self.assertTrue(EventFilter.matches_filters(event, filters))
    
    def test_matches_filters_multiple_criteria(self):
        """Test event matching with multiple filter criteria"""
        event = {
            "title": "Test Event",
            "location": "San Francisco",
            "level": "intermediate"
        }
        
        filters = {
            "locations": ["San Francisco"],
            "levels": ["intermediate"]
        }
        
        self.assertTrue(EventFilter.matches_filters(event, filters))
        
        # Fail on one criterion
        filters_fail = {
            "locations": ["San Francisco"],
            "levels": ["advanced"]
        }
        self.assertFalse(EventFilter.matches_filters(event, filters_fail))


class TestPublisherSideFiltering(unittest.TestCase):
    """Test cases for publisher-side filtering functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.event = {
            "event_id": "E123",
            "title": "AI Hackathon",
            "topic": "hackathon.aiml",
            "location": "San Francisco",
            "level": "intermediate"
        }
        
        self.subscriptions = [
            {
                "user_id": "U1",
                "topic": "hackathon.aiml",
                "channels": ["app", "email"],
                "filters": {}
            },
            {
                "user_id": "U2",
                "topic": "hackathon.*",
                "channels": ["app"],
                "filters": {"locations": ["San Francisco"]}
            },
            {
                "user_id": "U3",
                "topic": "jobs.internship",
                "channels": ["app", "email", "sms"],
                "filters": {}
            },
            {
                "user_id": "U4",
                "topic": "hackathon.aiml",
                "channels": ["email"],
                "filters": {"levels": ["advanced"]}  # Won't match
            }
        ]
    
    def test_get_subscribers_for_event(self):
        """Test getting filtered subscribers for an event"""
        subscribers = get_subscribers_for_event(self.event, self.subscriptions)
        
        # Should match U1 and U2, not U3 (wrong topic) or U4 (wrong level)
        self.assertEqual(len(subscribers), 2)
        
        user_ids = [s['user_id'] for s in subscribers]
        self.assertIn("U1", user_ids)
        self.assertIn("U2", user_ids)
        self.assertNotIn("U3", user_ids)
        self.assertNotIn("U4", user_ids)
    
    def test_build_notification_payload(self):
        """Test building notification payload"""
        subscribers = [
            {"user_id": "U1", "channels": ["app", "email"]},
            {"user_id": "U2", "channels": ["app", "sms"]}
        ]
        
        payload = build_notification_payload(self.event, subscribers, priority="high")
        
        self.assertEqual(payload['event_id'], "E123")
        self.assertEqual(payload['title'], "AI Hackathon")
        self.assertEqual(len(payload['subscriber_ids']), 2)
        self.assertIn("U1", payload['subscriber_ids'])
        self.assertIn("U2", payload['subscriber_ids'])
        self.assertEqual(payload['priority'], "high")
        
        # Channels should be aggregated
        self.assertIn("app", payload['channels'])
        self.assertIn("email", payload['channels'])
        self.assertIn("sms", payload['channels'])


if __name__ == '__main__':
    unittest.main()


