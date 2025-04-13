#!/usr/bin/env python3
"""
LLM Test Example

This example demonstrates how to use the LLMHandler to interact with a language model
using the AnyRobo framework.
"""

import argparse
import time
from typing import Any, Dict, Optional

from anyrobo.brain.llm_handler import LLMHandler
from anyrobo.utils.events import EventBus


class LLMTest:
    """
    Test class for interacting with the LLMHandler.

    This class demonstrates how to initialize an LLM handler, send messages,
    and process the responses with event handling.
    """

    def __init__(
        self,
        model_name: str = "llama3.2",
        system_prompt: Optional[str] = None,
        debug: bool = True,
    ) -> None:
        """
        Initialize the LLM test.

        Args:
            model_name: Name of the LLM model to use
            system_prompt: Optional system prompt for the LLM
            debug: Enable debug messages
        """
        # Enable debug printing
        self.debug = debug

        # Create the central event bus
        self.event_bus = EventBus()

        self._log("Creating LLM handler")
        # Create LLM handler
        self.llm = LLMHandler(
            model_name=model_name,
            system_prompt=system_prompt,
        )

        # Override the default event bus
        self._log("Setting custom event bus")
        self.llm._event_bus = self.event_bus

        # Register event handlers
        self._register_event_handlers()

        # Tracking variables
        self.current_response_id = ""
        self.llm_response_buffer = ""

        # Model loading status
        self.llm_model_loaded = False

    def _log(self, message: str) -> None:
        """Print debug message if debug is enabled."""
        if self.debug:
            print(f"[DEBUG] {message}")

    def _register_event_handlers(self) -> None:
        """Register event handlers for LLM events."""
        self._log("Registering event handlers")
        # LLM events
        self.event_bus.subscribe(LLMHandler.MODEL_LOADED, self._on_llm_model_loaded)
        self.event_bus.subscribe(LLMHandler.RESPONSE_STARTED, self._on_llm_response_started)
        self.event_bus.subscribe(LLMHandler.RESPONSE_CHUNK, self._on_llm_response_chunk)
        self.event_bus.subscribe(LLMHandler.RESPONSE_COMPLETED, self._on_llm_response_completed)
        self.event_bus.subscribe(LLMHandler.RESPONSE_ERROR, self._on_llm_response_error)

    def _on_llm_model_loaded(self, data: Dict[str, Any]) -> None:
        """Handle LLM model loaded event."""
        model = data.get("model", "unknown") if data else "unknown"
        print(f"[INFO] LLM model loaded successfully: {model}")
        self.llm_model_loaded = True

    def _on_llm_response_started(self, data: Dict[str, Any]) -> None:
        """Handle LLM response started event."""
        response_id = data.get("response_id", "unknown") if data else "unknown"
        print(f"[INFO] LLM response generation started (ID: {response_id[:8]})")

        # Reset the response buffer when starting a new response
        self.llm_response_buffer = ""

    def _on_llm_response_chunk(self, data: Dict[str, Any]) -> None:
        """Handle LLM response chunk event."""
        response_id = data.get("response_id", "unknown") if data else "unknown"
        chunk = data.get("chunk", "") if data else ""

        # Print chunk without newline to show streaming
        print(chunk, end="", flush=True)

        # Accumulate chunks
        self.llm_response_buffer += chunk

    def _on_llm_response_completed(self, data: Dict[str, Any]) -> None:
        """Handle LLM response completed event."""
        response_id = data.get("response_id", "unknown") if data else "unknown"
        response = data.get("response", "") if data else ""

        print("\n\n[INFO] LLM response completed (ID: {})".format(response_id[:8]))

        # Make sure we have the response in our buffer
        if not self.llm_response_buffer and response:
            self.llm_response_buffer = response

    def _on_llm_response_error(self, data: Dict[str, Any]) -> None:
        """Handle LLM response error event."""
        error = data.get("error", "Unknown error") if data else "Unknown error"
        print(f"[ERROR] LLM response error: {error}")

    def generate_response(self, user_message: str) -> None:
        """
        Generate a response to the given user message.

        Args:
            user_message: Message to send to the LLM
        """
        print(f"\n[USER] {user_message}")
        self.current_response_id = self.llm.generate_response(user_message)
        self._log(f"Response ID: {self.current_response_id}")

    def wait_for_model_loading(self, timeout: int = 10) -> bool:
        """
        Wait for the LLM model to be loaded.

        Args:
            timeout: Maximum seconds to wait

        Returns:
            bool: True if model was loaded, False if timed out
        """
        start_time = time.time()
        while not self.llm_model_loaded and time.time() - start_time < timeout:
            # Check both the event flag and the model_loaded attribute if available
            print(f"Model loaded: {self.llm.model_loaded}")
            if hasattr(self.llm, "model_loaded") and self.llm.model_loaded:
                self.llm_model_loaded = True
                break

            print("Waiting for model to load...")
            time.sleep(1)

        return self.llm_model_loaded

    def show_conversation_history(self) -> None:
        """Display the current conversation history."""
        print("\n----- Conversation History -----")
        for msg in self.llm.get_history():
            role = msg["role"].upper()
            content = msg["content"]
            print(f"[{role}] {content}")
        print("-------------------------------\n")


def main():
    """Run the LLM test example."""
    parser = argparse.ArgumentParser(description="Test the AnyRobo LLM Handler")
    parser.add_argument("--model", type=str, default="llama3.2", help="LLM model to use")
    parser.add_argument(
        "--system-prompt",
        type=str,
        default="You are a helpful AI assistant. Be concise.",
        help="System prompt for the LLM",
    )
    args = parser.parse_args()

    # Create the test instance
    test = LLMTest(
        model_name=args.model,
        system_prompt=args.system_prompt,
    )

    # Wait for model to load
    if not test.wait_for_model_loading():
        print("Model loading timed out. Make sure Ollama is running.")
        return

    # Interactive loop
    print("\nEnter messages for the LLM. Type 'exit' to quit, 'history' to see conversation.")
    while True:
        user_input = input("\nYou: ").strip()

        if not user_input:
            continue
        elif user_input.lower() == "exit":
            break
        elif user_input.lower() == "history":
            test.show_conversation_history()
        else:
            test.generate_response(user_input)
            # Add a small delay to ensure all events are processed
            time.sleep(0.5)


if __name__ == "__main__":
    main()
