# tests/test_multivision_router_capabilities.py
"""Automated tests for MultiVision Multimodal Planning & Routing Engine."""

import pytest
from src.multivision.multimodal_router import plan_multimodal_routing, TaskCategory


def test_routing_text_reasoning():
    plan = plan_multimodal_routing(
        message="Prove that the square root of 2 is irrational using a step-by-step mathematical proof."
    )
    assert plan.detected_task == TaskCategory.REASONING
    assert "text" in plan.input_modalities
    assert plan.selected_model is not None


def test_routing_vision_image_attachment():
    plan = plan_multimodal_routing(
        message="Extract text and objects from this schematic diagram",
        file_names=["architecture_diagram.png"]
    )
    assert plan.detected_task in (TaskCategory.IMAGE_ANALYSIS, TaskCategory.OCR)
    assert "image" in plan.input_modalities
    assert "png" in plan.file_types
    assert plan.selected_model is not None


def test_routing_document_pdf():
    plan = plan_multimodal_routing(
        message="Summarize this financial quarterly filing and extract the EBITDA table",
        file_names=["Q4_Report.pdf"]
    )
    assert plan.detected_task in (TaskCategory.PDF_ANALYSIS, TaskCategory.DOCUMENT_ANALYSIS)
    assert "pdf" in plan.input_modalities
    assert "pdf" in plan.file_types


def test_routing_audio_transcription():
    plan = plan_multimodal_routing(
        message="Transcribe this voice meeting recording and list the action items",
        file_names=["meeting_call.mp3"]
    )
    assert plan.detected_task in (TaskCategory.AUDIO_TRANSCRIPTION, TaskCategory.AUDIO_ANALYSIS)
    assert "audio" in plan.input_modalities


def test_routing_video_scene():
    plan = plan_multimodal_routing(
        message="Decompose the scenes and understand events in this video recording",
        file_names=["demo_recording.mp4"]
    )
    assert plan.detected_task in (TaskCategory.VIDEO_ANALYSIS, TaskCategory.VIDEO_UNDERSTANDING)
    assert "video" in plan.input_modalities


def test_routing_coding():
    plan = plan_multimodal_routing(
        message="Write a FastAPI asynchronous router endpoint with Pydantic v2 validation and error handling in Python"
    )
    assert plan.detected_task == TaskCategory.CODING
    assert plan.detected_task.value == "CODING"
