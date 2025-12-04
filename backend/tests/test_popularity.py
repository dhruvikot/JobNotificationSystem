"""
Unit Tests for Popularity Tracking

Tests the popularity tracking and priority assignment including:
- Topic count incrementing
- Priority calculation
- In-memory storage
"""

import unittest
from backend.libs.popularity import PopularityTracker


class TestPopularityTracker(unittest.TestCase):
    """Test cases for Popularity Tracking"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Use in-memory storage for testing
        self.tracker = PopularityTracker(use_dynamodb=False)
    
    def test_initialization(self):
        """Test tracker initialization"""
        self.assertIsNotNone(self.tracker)
        self.assertEqual(len(self.tracker.memory_store), 0)
    
    def test_increment_topic(self):
        """Test incrementing topic count"""
        count = self.tracker.increment_topic("hackathon.aiml")
        self.assertEqual(count, 1)
        
        count = self.tracker.increment_topic("hackathon.aiml")
        self.assertEqual(count, 2)
    
    def test_increment_topic_custom_amount(self):
        """Test incrementing by custom amount"""
        count = self.tracker.increment_topic("hackathon.aiml", amount=5)
        self.assertEqual(count, 5)
        
        count = self.tracker.increment_topic("hackathon.aiml", amount=3)
        self.assertEqual(count, 8)
    
    def test_get_count(self):
        """Test getting topic count"""
        self.tracker.increment_topic("hackathon.aiml", amount=10)
        
        count = self.tracker.get_count("hackathon.aiml")
        self.assertEqual(count, 10)
        
        # Non-existent topic
        count = self.tracker.get_count("nonexistent.topic")
        self.assertEqual(count, 0)
    
    def test_get_priority_low(self):
        """Test priority calculation for low count"""
        self.tracker.increment_topic("topic1", amount=5)
        priority = self.tracker.get_priority("topic1")
        self.assertEqual(priority, "low")
    
    def test_get_priority_medium(self):
        """Test priority calculation for medium count"""
        self.tracker.increment_topic("topic2", amount=30)
        priority = self.tracker.get_priority("topic2")
        self.assertEqual(priority, "low")  # Still low, threshold is 50
        
        self.tracker.increment_topic("topic2", amount=25)
        priority = self.tracker.get_priority("topic2")
        self.assertEqual(priority, "medium")
    
    def test_get_priority_high(self):
        """Test priority calculation for high count"""
        self.tracker.increment_topic("topic3", amount=150)
        priority = self.tracker.get_priority("topic3")
        self.assertEqual(priority, "high")
    
    def test_get_topic_info(self):
        """Test getting complete topic information"""
        self.tracker.increment_topic("hackathon.aiml", amount=60)
        
        info = self.tracker.get_topic_info("hackathon.aiml")
        
        self.assertEqual(info['topic'], "hackathon.aiml")
        self.assertEqual(info['count'], 60)
        self.assertEqual(info['priority'], "medium")
        self.assertIn('last_updated', info)
    
    def test_get_top_topics(self):
        """Test getting top topics"""
        self.tracker.increment_topic("topic1", amount=100)
        self.tracker.increment_topic("topic2", amount=50)
        self.tracker.increment_topic("topic3", amount=25)
        self.tracker.increment_topic("topic4", amount=75)
        
        top_topics = self.tracker.get_top_topics(limit=3)
        
        self.assertEqual(len(top_topics), 3)
        # Should be sorted by count descending
        self.assertEqual(top_topics[0]['topic'], "topic1")
        self.assertEqual(top_topics[1]['topic'], "topic4")
        self.assertEqual(top_topics[2]['topic'], "topic2")
    
    def test_reset_topic(self):
        """Test resetting topic count"""
        self.tracker.increment_topic("hackathon.aiml", amount=50)
        self.tracker.reset_topic("hackathon.aiml")
        
        count = self.tracker.get_count("hackathon.aiml")
        self.assertEqual(count, 0)
    
    def test_multiple_topics(self):
        """Test tracking multiple topics"""
        topics = ["hackathon.aiml", "jobs.internship", "careerfair.tech"]
        
        for topic in topics:
            self.tracker.increment_topic(topic, amount=10)
        
        for topic in topics:
            count = self.tracker.get_count(topic)
            self.assertEqual(count, 10)
    
    def test_custom_thresholds(self):
        """Test custom priority thresholds"""
        custom_tracker = PopularityTracker(
            use_dynamodb=False,
            thresholds={"low": 5, "medium": 20, "high": 50}
        )
        
        custom_tracker.increment_topic("topic", amount=3)
        self.assertEqual(custom_tracker.get_priority("topic"), "low")
        
        custom_tracker.increment_topic("topic", amount=10)
        self.assertEqual(custom_tracker.get_priority("topic"), "medium")
        
        custom_tracker.increment_topic("topic", amount=40)
        self.assertEqual(custom_tracker.get_priority("topic"), "high")


if __name__ == '__main__':
    unittest.main()



