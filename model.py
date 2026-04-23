"""DialoGPT model wrapper for conversational inference."""

from __future__ import annotations

import logging
import re
from typing import Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from config import config

logger = logging.getLogger(__name__)


def _is_low_quality_response(text: str) -> bool:
    if not text.strip():
        return True
    words = text.split()
    if not words:
        return True
    alnum_chars = sum(ch.isalnum() or ch.isspace() for ch in text)
    alnum_ratio = alnum_chars / max(len(text), 1)
    has_long_noise = bool(re.search(r"[a-zA-Z0-9]{16,}", text))
    has_repeated_noise = bool(re.search(r"(.)\1{5,}", text))
    noisy_word_ratio = sum(
        1
        for word in words
        if len(word) > 12 or any(ch.isdigit() for ch in word) or re.search(r"[A-Z]{3,}", word)
    ) / len(words)
    return (
        alnum_ratio < 0.72
        or has_long_noise
        or has_repeated_noise
        or noisy_word_ratio > 0.25
    )


class ChatModel:
    """Stateful chatbot model with bounded conversation history."""

    def __init__(self, model_name: str, max_history: int) -> None:
        self.model_name = model_name
        self.max_history = max_history
        self.chat_history_ids: torch.Tensor | None = None
        self.step = 0

        logger.info("Loading tokenizer and model: %s", self.model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_name)

        if self.tokenizer.pad_token is None:
            logger.debug("Tokenizer pad token missing, assigning EOS token as PAD token.")
            self.tokenizer.pad_token = self.tokenizer.eos_token

        self.model.eval()
        logger.info("Model loaded and set to eval mode.")

    def generate_response(self, user_input: str) -> str:
        """Generate a response for user input and update history."""
        cleaned_input = user_input.strip()
        if not cleaned_input:
            raise ValueError("Input message cannot be empty.")

        logger.debug("Generating response for step=%s", self.step)
        eos_text = self.tokenizer.eos_token or ""
        new_user_input_ids = self.tokenizer.encode(
            cleaned_input + eos_text,
            return_tensors="pt",
        )

        if self.chat_history_ids is not None and self.step < self.max_history:
            bot_input_ids = torch.cat([self.chat_history_ids, new_user_input_ids], dim=-1)
            logger.debug("Using existing history for generation.")
        else:
            bot_input_ids = new_user_input_ids
            if self.chat_history_ids is not None:
                logger.debug("Max history reached. Starting fresh context window.")
                self.step = 0

        max_context_tokens = 1000
        if bot_input_ids.shape[-1] > max_context_tokens:
            logger.warning(
                "Context exceeded %s tokens (%s). Truncating to recent window.",
                max_context_tokens,
                bot_input_ids.shape[-1],
            )
            bot_input_ids = bot_input_ids[:, -max_context_tokens:]

        try:
            attention_mask = torch.ones_like(bot_input_ids)
            with torch.no_grad():
                self.chat_history_ids = self.model.generate(
                    bot_input_ids,
                    attention_mask=attention_mask,
                    max_new_tokens=min(config.MAX_NEW_TOKENS, 50),
                    repetition_penalty=config.REPETITION_PENALTY,
                    do_sample=False,
                    no_repeat_ngram_size=3,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                )
        except RuntimeError as exc:
            if "out of memory" in str(exc).lower():
                logger.exception("OOM during generation. Clearing history.")
                self.clear_history()
                return "The conversation was reset due to memory pressure. Please try again."
            logger.exception("Runtime error while generating response.")
            raise

        new_tokens = self.chat_history_ids[:, bot_input_ids.shape[-1] :]
        response = self.tokenizer.decode(new_tokens[0], skip_special_tokens=True).strip()

        if _is_low_quality_response(response):
            logger.warning("Low quality response detected. Returning fallback and clearing history.")
            self.clear_history()
            response = (
                "I want to give you a better answer. "
                "Could you ask that again in a short, specific sentence?"
            )

        if not response:
            logger.warning("Empty response generated, using fallback.")
            response = "I'm not sure what to say. Could you rephrase that?"

        self.step += 1
        logger.debug("Response generated successfully. step=%s", self.step)
        return response

    def clear_history(self) -> None:
        """Reset conversation history."""
        self.chat_history_ids = None
        self.step = 0
        logger.info("Chat history cleared.")

    def get_model_info(self) -> dict[str, Any]:
        """Return model metadata and runtime state."""
        parameter_count = sum(p.numel() for p in self.model.parameters())
        return {
            "model_name": self.model_name,
            "max_history": self.max_history,
            "current_step": self.step,
            "has_history": self.chat_history_ids is not None,
            "parameter_count": parameter_count,
        }
