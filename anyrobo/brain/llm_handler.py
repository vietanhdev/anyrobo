"""
LLM Handler for the AnyRobo framework.

Handles interactions with language models for generating responses.
"""

import re
import threading
import time
from typing import Dict, List, Optional

from anyrobo.models.loader import ensure_ollama_model
from anyrobo.utils.events import Component

# Default import for Ollama - can be extended to support other providers
try:
    from ollama import chat, list

    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    print("Warning: Ollama not available. LLM functionality will be limited.")


class LLMHandler(Component):
    """
    Handler for Language Model interactions.

    Manages communication with LLMs, tracking conversation history,
    and streaming responses.
    """

    # Event topics
    RESPONSE_STARTED = "llm.response.started"
    RESPONSE_CHUNK = "llm.response.chunk"
    RESPONSE_COMPLETED = "llm.response.completed"
    RESPONSE_ERROR = "llm.response.error"
    MODEL_LOADED = "llm.model.loaded"

    def __init__(self, model_name: str = "llama3.2", system_prompt: Optional[str] = None) -> None:
        """
        Initialize the LLM handler.

        Args:
            model_name: Name of the LLM model to use
            system_prompt: Optional system prompt to use for all conversations
        """
        super().__init__()
        self.model_name = model_name
        self.system_prompt = system_prompt or ""
        self.messages: List[Dict[str, str]] = []

        # If there's a system prompt, add it to messages
        if self.system_prompt:
            self.messages.append({"role": "system", "content": self.system_prompt})

        # State tracking
        self.is_generating = False
        self.current_response_id = ""
        self._generation_lock = threading.Lock()

        # Model loading status
        self.model_loaded = False

        # Start background thread to ensure model is loaded
        self._initialize_model()

    def _initialize_model(self) -> None:
        """Initialize the LLM model in a background thread."""
        if not OLLAMA_AVAILABLE:
            print("Ollama not available, skipping model initialization")
            return

        def load_model():
            try:
                print(f"Loading model {self.model_name}")
                ensure_ollama_model(self.model_name)
                # Check if model is available using Python Ollama client
                print("Checking if model is available")
                models_response = list()
                print(f"Models response: {models_response}")

                model_available = any(
                    self.model_name in model.get("model") for model in models_response["models"]
                )
                if model_available:
                    self.model_loaded = True
                    self.publish_event(self.MODEL_LOADED, {"model": self.model_name})
            except Exception as e:
                print(f"Error loading model {self.model_name}: {e}")
                self.model_loaded = False

        threading.Thread(target=load_model, daemon=True).start()

    def add_message(self, role: str, content: str) -> None:
        """
        Add a message to the conversation history.

        Args:
            role: Role of the message sender (user, assistant, system)
            content: Content of the message
        """
        # If role is system, replace any existing system message or add at the beginning
        if role == "system":
            # Remove any existing system messages
            self.messages = [msg for msg in self.messages if msg["role"] != "system"]
            # Add at the beginning
            self.messages.insert(0, {"role": role, "content": content})
        else:
            # Add regular message to the end
            self.messages.append({"role": role, "content": content})

    def clear_history(self) -> None:
        """Clear the conversation history but preserve the system prompt."""
        system_prompts = [msg for msg in self.messages if msg["role"] == "system"]
        self.messages = system_prompts

    def get_history(self) -> List[Dict[str, str]]:
        """
        Get the conversation history.

        Returns:
            List of message dictionaries
        """
        return self.messages.copy()

    def generate_response(self, user_message: Optional[str] = None) -> str:
        """
        Generate a response to the latest message.

        Args:
            user_message: Optional new user message to add before generating

        Returns:
            str: Response ID that can be used to track this response
        """
        # Don't allow multiple simultaneous generations
        with self._generation_lock:
            if self.is_generating:
                print("Response generation already in progress")
                return ""

            self.is_generating = True
            self.current_response_id = f"response_{int(time.time())}"

        # Add user message if provided
        if user_message:
            self.add_message("user", user_message)

        # Start response generation in a background thread
        threading.Thread(target=self._generate_response_thread, daemon=True).start()

        return self.current_response_id

    def _generate_response_thread(self) -> None:
        """Generate a response in a background thread."""
        if not OLLAMA_AVAILABLE:
            self.publish_event(
                self.RESPONSE_ERROR,
                {"response_id": self.current_response_id, "error": "Ollama not available"},
            )
            self.is_generating = False
            return

        try:
            # Notify listeners that response generation has started
            self.publish_event(self.RESPONSE_STARTED, {"response_id": self.current_response_id})

            # Generate response with streaming
            response_text = ""

            # Generate streaming response using Ollama
            stream = chat(
                model=self.model_name,
                messages=self.messages,
                stream=True,
            )

            # Pattern for sentence boundaries
            sentence_pattern = re.compile(r"([.!?])\s+|([.!?])$")

            for chunk in stream:
                # Get chunk content
                content = chunk["message"]["content"]

                # Accumulate total response
                response_text += content

                # Publish chunk event
                self.publish_event(
                    self.RESPONSE_CHUNK,
                    {
                        "response_id": self.current_response_id,
                        "chunk": content,
                        "response_so_far": response_text,
                    },
                )

            # Add the complete response to our conversation history
            self.add_message("assistant", response_text)

            # Publish completion event with the full response
            self.publish_event(
                self.RESPONSE_COMPLETED,
                {"response_id": self.current_response_id, "response": response_text},
            )

        except Exception as e:
            print(f"Error generating response: {e}")
            self.publish_event(
                self.RESPONSE_ERROR, {"response_id": self.current_response_id, "error": str(e)}
            )

        finally:
            # Reset state
            self.is_generating = False

    def cancel_generation(self) -> bool:
        """
        Cancel ongoing response generation.

        Returns:
            bool: True if generation was canceled, False if no generation was in progress
        """
        if not self.is_generating:
            return False

        # TODO: Add actual cancellation mechanism when Ollama supports it
        # For now, we just mark it as not generating
        self.is_generating = False

        self.publish_event(
            self.RESPONSE_ERROR,
            {"response_id": self.current_response_id, "error": "Response generation canceled"},
        )

        return True
