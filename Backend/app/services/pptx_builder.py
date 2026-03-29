from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from app.models import DeckBlueprint


INTENT_COLORS: dict[str, tuple[int, int, int]] = {
    "technical": (29, 78, 216),
    "business": (22, 101, 52),
    "academic": (55, 65, 81),
    "creative": (194, 65, 12),
}


class PptxDeckBuilder:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def build(self, *, deck: DeckBlueprint, topic: str, intent: str) -> Path:
        try:
            from pptx import Presentation
            from pptx.dml.color import RGBColor
            from pptx.enum.text import PP_ALIGN
            from pptx.util import Inches, Pt
        except ImportError as exc:
            raise RuntimeError(
                "python-pptx is not installed. Run `uv pip install -r requirements.txt` in Backend."
            ) from exc

        self.output_dir.mkdir(parents=True, exist_ok=True)
        prs = Presentation()
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)

        accent = INTENT_COLORS.get(intent, (29, 78, 216))

        for slide_plan in deck.slides:
            slide = prs.slides.add_slide(prs.slide_layouts[6])
            background = slide.background.fill
            background.solid()
            background.fore_color.rgb = RGBColor(247, 248, 250)

            top_band = slide.shapes.add_shape(
                1,
                Inches(0),
                Inches(0),
                prs.slide_width,
                Inches(0.45),
            )
            top_band.fill.solid()
            top_band.fill.fore_color.rgb = RGBColor(*accent)
            top_band.line.color.rgb = RGBColor(*accent)

            title_box = slide.shapes.add_textbox(Inches(0.7), Inches(0.7), Inches(8.6), Inches(0.8))
            title_frame = title_box.text_frame
            title_run = title_frame.paragraphs[0].add_run()
            title_run.text = slide_plan.title
            title_run.font.size = Pt(24)
            title_run.font.bold = True
            title_run.font.color.rgb = RGBColor(17, 24, 39)

            objective_box = slide.shapes.add_textbox(Inches(0.7), Inches(1.35), Inches(8.8), Inches(0.6))
            objective_frame = objective_box.text_frame
            objective_frame.word_wrap = True
            objective_run = objective_frame.paragraphs[0].add_run()
            objective_run.text = slide_plan.objective
            objective_run.font.size = Pt(12)
            objective_run.font.color.rgb = RGBColor(71, 85, 105)

            bullet_box = slide.shapes.add_textbox(Inches(0.8), Inches(2.0), Inches(7.0), Inches(3.9))
            bullet_frame = bullet_box.text_frame
            bullet_frame.word_wrap = True
            for index, point in enumerate(slide_plan.key_points):
                paragraph = bullet_frame.paragraphs[0] if index == 0 else bullet_frame.add_paragraph()
                paragraph.text = point
                paragraph.level = 0
                paragraph.font.size = Pt(18)
                paragraph.font.color.rgb = RGBColor(31, 41, 55)
                paragraph.space_after = Pt(10)

            visual_box = slide.shapes.add_textbox(Inches(8.2), Inches(1.85), Inches(4.2), Inches(3.4))
            visual_fill = visual_box.fill
            visual_fill.solid()
            visual_fill.fore_color.rgb = RGBColor(255, 255, 255)
            visual_box.line.color.rgb = RGBColor(203, 213, 225)
            visual_frame = visual_box.text_frame
            visual_frame.word_wrap = True
            visual_header = visual_frame.paragraphs[0].add_run()
            visual_header.text = f"{slide_plan.visual_type.replace('_', ' ').title()} concept"
            visual_header.font.size = Pt(15)
            visual_header.font.bold = True
            visual_header.font.color.rgb = RGBColor(*accent)
            visual_body = visual_frame.add_paragraph()
            visual_body.text = slide_plan.visual_brief
            visual_body.font.size = Pt(13)
            visual_body.font.color.rgb = RGBColor(51, 65, 85)

            notes_box = slide.shapes.add_textbox(Inches(8.2), Inches(5.45), Inches(4.2), Inches(1.15))
            notes_frame = notes_box.text_frame
            notes_frame.word_wrap = True
            notes_title = notes_frame.paragraphs[0].add_run()
            notes_title.text = "Speaker note"
            notes_title.font.size = Pt(12)
            notes_title.font.bold = True
            notes_title.font.color.rgb = RGBColor(*accent)
            notes_body = notes_frame.add_paragraph()
            notes_body.text = slide_plan.speaker_notes
            notes_body.font.size = Pt(11)
            notes_body.font.color.rgb = RGBColor(71, 85, 105)

            footer_box = slide.shapes.add_textbox(Inches(0.7), Inches(6.8), Inches(12.0), Inches(0.35))
            footer_frame = footer_box.text_frame
            footer_frame.paragraphs[0].alignment = PP_ALIGN.LEFT
            footer_run = footer_frame.paragraphs[0].add_run()
            footer_run.text = (
                f"Slide {slide_plan.slide_number}  |  Evidence: "
                + (", ".join(slide_plan.evidence_orbs) if slide_plan.evidence_orbs else "reasoned synthesis")
            )
            footer_run.font.size = Pt(10)
            footer_run.font.color.rgb = RGBColor(100, 116, 139)

        filename = f"{self._slugify(topic)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pptx"
        output_path = self.output_dir / filename
        prs.save(output_path)
        return output_path

    @staticmethod
    def _slugify(value: str) -> str:
        cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
        return cleaned[:80] or "presentation"
