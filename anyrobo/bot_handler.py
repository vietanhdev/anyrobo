"""
Bot Handler for the AnyRobo framework.

Coordinates speech recognition, text-to-speech, and language model components
to create a complete conversational assistant.
"""

import re
import threading
import time
from typing import Any, Dict, Optional

from anyrobo.brain.llm_handler import LLMHandler
from anyrobo.speech.stt_handler import STTHandler
from anyrobo.speech.tts_handler import TTSHandler
from anyrobo.utils.events import Component


class BotHandler(Component):
    """
    Main coordinator for voice assistant functionality.

    Manages communication between STT, LLM, and TTS components to create
    a complete voice-based assistant.
    """

    # Event topics
    STATUS_CHANGED = "bot.status.changed"
    USER_MESSAGE = "bot.user.message"
    ASSISTANT_MESSAGE = "bot.assistant.message"
    ASSISTANT_MESSAGE_CHUNK = "bot.assistant.message.chunk"
    ERROR = "bot.error"

    def __init__(
        self,
        llm_handler: Optional[LLMHandler] = None,
        stt_handler: Optional[STTHandler] = None,
        tts_handler: Optional[TTSHandler] = None,
        model_name: str = "llama3.2",
        system_prompt: Optional[str] = None,
        debug: bool = False,
    ) -> None:
        """
        Initialize the bot handler.

        Args:
            llm_handler: Pre-initialized LLM handler
            stt_handler: Pre-initialized STT handler
            tts_handler: Pre-initialized TTS handler
            model_name: Name of the LLM model to use (only used if llm_handler not provided)
            system_prompt: Optional system prompt for the LLM (only used if llm_handler not provided)
            debug: Enable debug logging
        """
        super().__init__()

        # Debug mode
        self.debug = debug

        # State variables
        self.is_generating_response = False
        self.current_response_id = ""

        # Track if we own the handlers (created them) or if they were provided externally
        self._owns_llm_handler = llm_handler is None
        self._owns_stt_handler = stt_handler is None
        self._owns_tts_handler = tts_handler is None

        # Use provided handlers or create new ones
        self.llm_handler = llm_handler or LLMHandler(
            model_name=model_name, system_prompt=system_prompt
        )
        self.stt_handler = stt_handler or STTHandler()
        self.tts_handler = tts_handler or TTSHandler()

        # Setup event listeners
        self._setup_event_listeners()

        self._debug_log("Bot handler initialized")

    def _debug_log(self, message: str) -> None:
        """Print debug logs if debug mode is enabled."""
        if self.debug:
            print(f"[Bot] {message}")

    def _setup_event_listeners(self) -> None:
        """Set up event subscriptions for component communication."""
        # STT event listeners
        self.subscribe_to_event(
            self.stt_handler.LISTENING_STARTED, lambda _: self._update_status("Listening")
        )

        self.subscribe_to_event(
            self.stt_handler.LISTENING_STOPPED, lambda _: self._update_status("Online")
        )

        self.subscribe_to_event(
            self.stt_handler.LISTENING_PAUSED, lambda _: self._update_status("Paused")
        )

        self.subscribe_to_event(
            self.stt_handler.LISTENING_RESUMED, lambda _: self._update_status("Listening")
        )

        self.subscribe_to_event(
            self.stt_handler.TRANSCRIPTION_STARTED, lambda _: self._update_status("Processing")
        )

        self.subscribe_to_event(self.stt_handler.TRANSCRIPTION_RESULT, self._handle_transcription)

        # LLM event listeners
        self.subscribe_to_event(
            self.llm_handler.RESPONSE_STARTED, lambda _: self._update_status("Thinking")
        )

        self.subscribe_to_event(self.llm_handler.RESPONSE_CHUNK, self._handle_llm_chunk)

        self.subscribe_to_event(self.llm_handler.RESPONSE_COMPLETED, self._handle_llm_complete)

        # TTS event listeners
        self.subscribe_to_event(
            self.tts_handler.SPEECH_STARTED, lambda _: self._update_status("Speaking")
        )

        self.subscribe_to_event(self.tts_handler.SPEECH_ENDED, self._handle_speech_ended)

    def _update_status(self, status: str) -> None:
        """
        Update and publish the bot's status.

        Args:
            status: New status string
        """
        # Only update status if we're not in the middle of response generation,
        # unless it's a "Speaking" status (which should take priority)
        if not self.is_generating_response or status == "Speaking":
            self.publish_event(self.STATUS_CHANGED, {"status": status})

    def _handle_transcription(self, data: Dict[str, Any]) -> None:
        """
        Handle new transcription from STT.

        Args:
            data: Transcription data containing text and confidence
        """
        text = data.get("text", "").strip()
        if not text:
            return

        # Skip processing if TTS is playing - prevents overlap
        if self.tts_handler.is_speaking():
            self._debug_log("Skipping transcription while speaking")
            return

        # Skip if we're already generating a response
        if self.is_generating_response:
            self._debug_log("Skipping transcription during response generation")
            return

        # Publish user message
        self.publish_event(self.USER_MESSAGE, {"text": text})

        # Generate response
        self.generate_response(text)

    def _handle_llm_chunk(self, data: Dict[str, Any]) -> None:
        """
        Handle streaming chunk from LLM.

        Args:
            data: Chunk data including the chunk text and cumulative response
        """
        response_id = data.get("response_id", "")
        chunk = data.get("chunk", "")
        response_so_far = data.get("response_so_far", "")

        if not response_id or not chunk:
            return

        # Publish the updated response text for UI display
        self.publish_event(
            self.ASSISTANT_MESSAGE_CHUNK,
            {"response_id": response_id, "chunk": chunk, "text": response_so_far},
        )

        # Process sentences from the response for real-time TTS
        self._process_response_chunk(chunk)

    def _handle_llm_complete(self, data: Dict[str, Any]) -> None:
        """
        Handle LLM response completion.

        Args:
            data: Response data including the complete response text
        """
        response_id = data.get("response_id", "")
        response = data.get("response", "")

        if not response_id:
            return

        # Publish the complete response
        self.publish_event(self.ASSISTANT_MESSAGE, {"response_id": response_id, "text": response})

        # Make sure STT is paused while TTS is speaking
        self._debug_log("Ensuring STT is paused while speaking")
        self.stt_handler.pause_listening()

        # Mark that no more chunks are coming
        self.tts_handler.finish_streaming()

        # Wait briefly to ensure audio processing is started
        time.sleep(0.2)

        # Wait for speech to complete in a separate thread
        threading.Thread(
            target=self._wait_for_speech_completion,
            args=(self.stt_handler.is_active(),),
            daemon=True,
        ).start()

    def _handle_speech_ended(self, data: Dict[str, Any]) -> None:
        """
        Handle speech ended event from TTS.

        Args:
            data: Speech event data
        """
        # Session ID from the event data
        session_id = data.get("session_id", "")

        # Check if we need to restart listening cycle
        if not self.is_generating_response:
            # Wait a moment for audio system to stabilize
            time.sleep(0.2)

            if not self.tts_handler.is_speaking():
                self._debug_log("Auto-resuming listening after speech ended")

                # If we were previously listening or not in an active state, start listening again
                if not self.stt_handler.is_listening:
                    self.start_listening()
                elif self.stt_handler.is_listening_paused:
                    self.stt_handler.resume_listening()
                    self._update_status("Listening")

                # Publish event to notify that the system is ready for new input
                self.publish_event(self.STATUS_CHANGED, {"status": "Ready for input"})
        else:
            self._debug_log("Not auto-resuming listening - still generating response")

    def _wait_for_speech_completion(self, was_listening: bool) -> None:
        """
        Wait for speech to complete and handle state transitions.

        Args:
            was_listening: Whether listening was active before speech
        """
        try:
            # First check if TTS is actually speaking
            if self.tts_handler.is_speaking():
                self._debug_log("Waiting for speech to complete")

                # Wait for speech to complete with timeout
                self.tts_handler.wait_for_completion(timeout=30.0)

                # Small delay to stabilize audio system
                time.sleep(0.3)

            # Reset generating state
            self.is_generating_response = False

            # After response is spoken, automatically start listening again
            if not self.tts_handler.is_speaking():
                self._debug_log("Auto-starting listening after response")

                # Always restart listening for a continuous conversation flow
                if not self.stt_handler.is_listening:
                    self.start_listening()
                elif self.stt_handler.is_listening_paused:
                    self.stt_handler.resume_listening()

                self._update_status("Listening")
            else:
                self._update_status("Online")

        except Exception as e:
            print(f"Error waiting for speech completion: {e}")
            # Clean up state in case of error
            self.is_generating_response = False
            self._update_status("Online")

            # Try to recover by starting listening
            self.start_listening()

    def _process_response_chunk(self, text: str) -> None:
        """
        Process a chunk of response text for TTS.

        Intelligently groups text into complete sentences or phrases for smoother speech.

        Args:
            text: Text chunk to process
        """
        if not text.strip():
            return

        # Check if we have a complete sentence or phrase
        # Complete sentences end with ., !, ? followed by space or end of string
        sentence_ends = [".", "!", "?", ";", ":", "\n"]
        is_complete_unit = any(text.strip().endswith(end) for end in sentence_ends)

        # If it's a complete sentence or substantial phrase (with punctuation),
        # send it directly for speech synthesis
        if is_complete_unit or len(text) > 30:  # Longer chunks or complete sentences
            self.tts_handler.speak_streaming_response(text)
        else:
            # For short fragments that aren't complete sentences, we might want to buffer them
            # but for simplicity, we'll still send them for immediate playback
            # This could be improved with a buffering mechanism that collects text until
            # a complete sentence is formed
            self.tts_handler.speak_streaming_response(text)

    def _extract_sentences(self, text: str) -> tuple:
        """
        Extract complete sentences from text.

        Args:
            text: Text to process

        Returns:
            Tuple of (list of sentences, remaining text)
        """
        # Pattern for sentence boundaries
        sentence_pattern = re.compile(r"([.!?])\s+|([.!?])$")

        sentences = []
        last_end = 0

        # Find all sentence boundaries
        for match in sentence_pattern.finditer(text):
            end_pos = match.end()
            sentence = text[last_end:end_pos].strip()
            if sentence:
                sentences.append(sentence)
            last_end = end_pos

        # Get remaining text (incomplete sentence)
        remaining = text[last_end:].strip()

        # If the remaining text is very long without sentence breaks,
        # use clause boundaries to avoid too much buffering
        if remaining and len(remaining) > 80:
            # Look for clause breaks (commas, semicolons, etc.)
            clause_pattern = re.compile(r"([,;:])\s+|(\s+and\s+|\s+but\s+|\s+or\s+)")
            clause_matches = list(clause_pattern.finditer(remaining))

            if clause_matches:
                # Use the last clause break
                last_break = clause_matches[-1]
                break_pos = last_break.end()

                clause_text = remaining[:break_pos].strip()
                if clause_text:
                    sentences.append(clause_text)
                    remaining = remaining[break_pos:].strip()

        return sentences, remaining

    def generate_response(self, user_message: str) -> None:
        """
        Generate a response to the user message.

        Args:
            user_message: User's message to respond to
        """
        # Don't allow multiple simultaneous generations
        if self.is_generating_response:
            self._debug_log("Response generation already in progress")
            return

        self.is_generating_response = True

        # Make sure STT is paused during response generation
        if self.stt_handler.is_active():
            self._debug_log("Pausing listening for response generation")
            self.stt_handler.pause_listening()

        # Generate response via LLM
        self.current_response_id = self.llm_handler.generate_response(user_message)

    def speak_text(self, text: str) -> None:
        """
        Synthesize and play the given text.

        Args:
            text: Text to speak
        """
        # Skip if nothing to say
        if not text.strip():
            return

        # Temporarily pause listening if active
        was_listening = self.stt_handler.is_active()
        if was_listening:
            self._debug_log("Pausing listening during direct speech")
            self.stt_handler.pause_listening()

        # Delegate to TTS handler
        self.tts_handler.speak_text(text)

        # Resume listening when speech is done (in a new thread)
        def wait_and_resume():
            try:
                # Wait for speech to complete
                self.tts_handler.wait_for_completion(timeout=10.0)

                # Small delay to stabilize audio
                time.sleep(0.2)

                # Resume listening if it was active before
                if was_listening and not self.tts_handler.is_speaking():
                    self._debug_log("Resuming listening after direct speech")
                    self.stt_handler.resume_listening()
                    self._update_status("Listening")
            except Exception as e:
                print(f"Error in wait_and_resume: {e}")
                # Try to resume anyway
                if was_listening and not self.tts_handler.is_speaking():
                    self.stt_handler.resume_listening()

        threading.Thread(target=wait_and_resume, daemon=True).start()

    def toggle_listening(self) -> None:
        """Toggle STT listening on/off."""
        if self.stt_handler.is_active():
            self.stop_listening()
        else:
            self.start_listening()

    def start_listening(self) -> None:
        """Start STT listening."""
        # Don't start listening if TTS is playing
        if self.tts_handler.is_speaking():
            self._debug_log("Cannot start listening - TTS is speaking")
            return

        # Don't start if we're generating a response
        if self.is_generating_response:
            self._debug_log("Cannot start listening - generating response")
            return

        self._debug_log("Starting listening")
        self.stt_handler.start_listening()

    def stop_listening(self) -> None:
        """Stop STT listening."""
        self._debug_log("Stopping listening")
        self.stt_handler.stop_listening()

    def pause_listening(self) -> None:
        """Pause STT listening."""
        self._debug_log("Pausing listening")
        self.stt_handler.pause_listening()

    def resume_listening(self) -> None:
        """Resume STT listening if it was paused."""
        # Only resume if TTS is not speaking
        if self.tts_handler.is_speaking():
            self._debug_log("Cannot resume listening - TTS is speaking")
            return

        # Don't resume if we're generating a response
        if self.is_generating_response:
            self._debug_log("Cannot resume listening - generating response")
            return

        self._debug_log("Resuming listening")
        self.stt_handler.resume_listening()

    @property
    def is_listening(self) -> bool:
        """
        Check if STT is actively listening.

        Returns:
            bool: True if listening, False otherwise
        """
        return self.stt_handler.is_active()

    def cleanup(self) -> None:
        """Clean up resources when shutting down."""
        # Only clean up handlers we created
        if hasattr(self, "llm_handler") and self._owns_llm_handler:
            self.llm_handler.cleanup()

        if hasattr(self, "tts_handler") and self._owns_tts_handler:
            self.tts_handler.cleanup()

        if hasattr(self, "stt_handler") and self._owns_stt_handler:
            self.stt_handler.cleanup()

        # Clean up parent resources
        super().cleanup()
