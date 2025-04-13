"""
Event system for the AnyRobo framework.

Provides a simple pub-sub (event) mechanism to allow communication between components.
"""

import threading
import uuid
from typing import Any, Callable, Dict, Set, TypeVar

T = TypeVar("T")


class EventBus:
    """
    A centralized event bus for pub-sub pattern communication between components.

    Components can subscribe to topics and publish events to them. Events are
    delivered to all subscribers of a topic.
    """

    def __init__(self) -> None:
        """Initialize a new event bus."""
        self._subscribers: Dict[str, Dict[str, Callable[[Any], None]]] = {}
        self._lock = threading.RLock()

    def subscribe(self, topic: str, callback: Callable[[Any], None]) -> str:
        """
        Subscribe to a topic with a callback function.

        Args:
            topic: The topic to subscribe to
            callback: Function to call when an event is published to this topic

        Returns:
            str: Subscription ID for unsubscribing
        """
        subscription_id = str(uuid.uuid4())

        with self._lock:
            if topic not in self._subscribers:
                self._subscribers[topic] = {}

            self._subscribers[topic][subscription_id] = callback

        return subscription_id

    def unsubscribe(self, topic: str, subscription_id: str) -> bool:
        """
        Unsubscribe from a topic using the subscription ID.

        Args:
            topic: The topic to unsubscribe from
            subscription_id: The ID returned from subscribe()

        Returns:
            bool: True if successfully unsubscribed, False otherwise
        """
        with self._lock:
            if topic in self._subscribers and subscription_id in self._subscribers[topic]:
                del self._subscribers[topic][subscription_id]

                # Clean up empty topics
                if not self._subscribers[topic]:
                    del self._subscribers[topic]

                return True

        return False

    def publish(self, topic: str, data: Any = None) -> int:
        """
        Publish an event to a topic.

        Args:
            topic: The topic to publish to
            data: The data to send to subscribers

        Returns:
            int: Number of subscribers the event was delivered to
        """
        callbacks = []

        with self._lock:
            if topic in self._subscribers:
                callbacks = list(self._subscribers[topic].values())

        # Deliver events outside the lock to prevent deadlocks
        for callback in callbacks:
            try:
                callback(data)
            except Exception as e:
                print(f"Error in event handler for topic '{topic}': {e}")

        return len(callbacks)

    def clear_topic(self, topic: str) -> int:
        """
        Remove all subscribers from a topic.

        Args:
            topic: The topic to clear

        Returns:
            int: Number of subscribers removed
        """
        with self._lock:
            if topic in self._subscribers:
                count = len(self._subscribers[topic])
                del self._subscribers[topic]
                return count

        return 0

    def clear_all(self) -> None:
        """Remove all subscribers from all topics."""
        with self._lock:
            self._subscribers.clear()


# Global event bus instance
_global_event_bus = EventBus()


def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    return _global_event_bus


class EventSource:
    """
    A mixin class that provides publishing functionality to a component.

    Classes that inherit from this can easily publish events to the global event bus.
    """

    def __init__(self) -> None:
        """Initialize the event source."""
        self._event_bus = get_event_bus()

    def publish_event(self, topic: str, data: Any = None) -> int:
        """
        Publish an event to the specified topic.

        Args:
            topic: The topic to publish to
            data: The data to send to subscribers

        Returns:
            int: Number of subscribers the event was delivered to
        """
        return self._event_bus.publish(topic, data)


class EventListener:
    """
    A mixin class that provides subscription functionality to a component.

    Classes that inherit from this can easily subscribe to events from the global event bus.
    """

    def __init__(self) -> None:
        """Initialize the event listener."""
        self._event_bus = get_event_bus()
        self._subscriptions: Dict[str, Set[str]] = {}

    def subscribe_to_event(self, topic: str, callback: Callable[[Any], None]) -> str:
        """
        Subscribe to events on the specified topic.

        Args:
            topic: The topic to subscribe to
            callback: Function to call when an event is published to this topic

        Returns:
            str: Subscription ID for unsubscribing
        """
        subscription_id = self._event_bus.subscribe(topic, callback)

        if topic not in self._subscriptions:
            self._subscriptions[topic] = set()

        self._subscriptions[topic].add(subscription_id)

        return subscription_id

    def unsubscribe_from_event(self, topic: str, subscription_id: str) -> bool:
        """
        Unsubscribe from events on the specified topic.

        Args:
            topic: The topic to unsubscribe from
            subscription_id: The ID returned from subscribe_to_event()

        Returns:
            bool: True if successfully unsubscribed, False otherwise
        """
        result = self._event_bus.unsubscribe(topic, subscription_id)

        if result and topic in self._subscriptions:
            self._subscriptions[topic].discard(subscription_id)

            if not self._subscriptions[topic]:
                del self._subscriptions[topic]

        return result

    def unsubscribe_all(self) -> None:
        """Unsubscribe from all events this listener has subscribed to."""
        for topic, subscription_ids in list(self._subscriptions.items()):
            for subscription_id in list(subscription_ids):
                self._event_bus.unsubscribe(topic, subscription_id)

        self._subscriptions.clear()


class Component(EventSource, EventListener):
    """
    Base class for components that can both publish and subscribe to events.

    This class combines EventSource and EventListener to provide a complete
    pub-sub interface for components.
    """

    def __init__(self) -> None:
        """Initialize the component."""
        EventSource.__init__(self)
        EventListener.__init__(self)

    def cleanup(self) -> None:
        """Clean up resources, including event subscriptions."""
        self.unsubscribe_all()
