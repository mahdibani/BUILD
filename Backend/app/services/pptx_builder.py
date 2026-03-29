from __future__ import annotations

import re
from datetime import datetime
from io import BytesIO
from pathlib import Path

import httpx

from app.models import DeckBlueprint, RetrievalResult


INTENT_COLORS: dict[str, tuple[int, int, int]] = {
    "technical": (29, 78, 216),
    "business": (22, 101, 52),
    "academic": (55, 65, 81),
    "creative": (194, 65, 12),
}


class PptxDeckBuilder:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def build(
        self,
        *,
        deck: DeckBlueprint,
        topic: str,
        intent: str,
        context: list[RetrievalResult] | None = None,
    ) -> Path:
        try:
            from pptx import Presentation
            from pptx.dml.color import RGBColor
            from pptx.enum.shapes import MSO_SHAPE
            from pptx.enum.text import PP_ALIGN, MSO_AUTO_SIZE
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
        context_map = {self._orb_id(item): item for item in context or []}

        for index, slide_plan in enumerate(deck.slides):
            slide = prs.slides.add_slide(prs.slide_layouts[6])
            self._paint_background(slide, accent, prs.slide_width)

            title_box = slide.shapes.add_textbox(Inches(0.7), Inches(0.62), Inches(8.6), Inches(0.8))
            title_frame = title_box.text_frame
            title_frame.word_wrap = True
            title_run = title_frame.paragraphs[0].add_run()
            title_run.text = slide_plan.title
            title_run.font.size = Pt(24 if index else 28)
            title_run.font.bold = True
            title_run.font.color.rgb = RGBColor(17, 24, 39)

            objective_box = slide.shapes.add_textbox(Inches(0.7), Inches(1.25), Inches(8.7), Inches(0.5))
            objective_frame = objective_box.text_frame
            objective_run = objective_frame.paragraphs[0].add_run()
            objective_run.text = slide_plan.objective
            objective_run.font.size = Pt(12)
            objective_run.font.bold = True
            objective_run.font.color.rgb = RGBColor(*accent)

            summary_box = slide.shapes.add_textbox(Inches(0.75), Inches(1.75), Inches(7.2), Inches(1.25))
            summary_frame = summary_box.text_frame
            summary_frame.word_wrap = True
            summary_frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
            summary_run = summary_frame.paragraphs[0].add_run()
            summary_run.text = slide_plan.summary_paragraph
            summary_run.font.size = Pt(14)
            summary_run.font.color.rgb = RGBColor(51, 65, 85)

            bullet_box = slide.shapes.add_textbox(Inches(0.8), Inches(3.05), Inches(6.8), Inches(2.9))
            bullet_frame = bullet_box.text_frame
            bullet_frame.word_wrap = True
            bullet_frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
            for point_index, point in enumerate(slide_plan.key_points):
                paragraph = bullet_frame.paragraphs[0] if point_index == 0 else bullet_frame.add_paragraph()
                paragraph.text = point
                paragraph.level = 0
                paragraph.font.size = Pt(16)
                paragraph.font.color.rgb = RGBColor(31, 41, 55)
                paragraph.space_after = Pt(8)

            image_placed = self._place_visual_asset(
                slide=slide,
                slide_plan=slide_plan,
                context_map=context_map,
                accent=accent,
            )
            if not image_placed:
                self._render_visual_brief(slide=slide, slide_plan=slide_plan, accent=accent)

            notes_box = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE,
                Inches(7.85),
                Inches(5.55),
                Inches(4.6),
                Inches(0.95),
            )
            notes_box.fill.solid()
            notes_box.fill.fore_color.rgb = RGBColor(255, 255, 255)
            notes_box.line.color.rgb = RGBColor(203, 213, 225)
            notes_frame = notes_box.text_frame
            notes_frame.word_wrap = True
            notes_title = notes_frame.paragraphs[0].add_run()
            notes_title.text = "Speaker note"
            notes_title.font.size = Pt(11)
            notes_title.font.bold = True
            notes_title.font.color.rgb = RGBColor(*accent)
            notes_body = notes_frame.add_paragraph()
            notes_body.text = slide_plan.speaker_notes
            notes_body.font.size = Pt(10.5)
            notes_body.font.color.rgb = RGBColor(71, 85, 105)

            footer_box = slide.shapes.add_textbox(Inches(0.7), Inches(6.78), Inches(12.0), Inches(0.32))
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

    def _paint_background(self, slide, accent: tuple[int, int, int], slide_width) -> None:
        from pptx.dml.color import RGBColor
        from pptx.enum.shapes import MSO_SHAPE
        from pptx.util import Inches

        background = slide.background.fill
        background.solid()
        background.fore_color.rgb = RGBColor(247, 248, 250)

        top_band = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(0),
            Inches(0),
            slide_width,
            Inches(0.42),
        )
        top_band.fill.solid()
        top_band.fill.fore_color.rgb = RGBColor(*accent)
        top_band.line.color.rgb = RGBColor(*accent)

        orb = slide.shapes.add_shape(
            MSO_SHAPE.OVAL,
            Inches(9.4),
            Inches(0.55),
            Inches(3.1),
            Inches(3.1),
        )
        orb.fill.solid()
        orb.fill.fore_color.rgb = RGBColor(*accent)
        orb.fill.transparency = 0.84
        orb.line.fill.background()

    def _render_visual_brief(self, *, slide, slide_plan, accent: tuple[int, int, int]) -> None:
        from pptx.dml.color import RGBColor
        from pptx.enum.shapes import MSO_SHAPE
        from pptx.util import Inches, Pt

        visual_box = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(7.85),
            Inches(1.55),
            Inches(4.6),
            Inches(3.7),
        )
        visual_box.fill.solid()
        visual_box.fill.fore_color.rgb = RGBColor(255, 255, 255)
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

    def _place_visual_asset(self, *, slide, slide_plan, context_map: dict[str, RetrievalResult], accent: tuple[int, int, int]) -> bool:
        from pptx.dml.color import RGBColor
        from pptx.enum.shapes import MSO_SHAPE
        from pptx.util import Inches, Pt

        image_url = self._select_image_url(slide_plan.evidence_orbs, context_map)
        if not image_url:
            return False

        image_bytes = self._download_image(image_url)
        if not image_bytes:
            return False

        slide.shapes.add_picture(BytesIO(image_bytes), Inches(7.85), Inches(1.55), width=Inches(4.6), height=Inches(3.7))
        caption = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(8.1),
            Inches(4.8),
            Inches(4.1),
            Inches(0.45),
        )
        caption.fill.solid()
        caption.fill.fore_color.rgb = RGBColor(255, 255, 255)
        caption.fill.transparency = 0.12
        caption.line.color.rgb = RGBColor(*accent)
        caption_frame = caption.text_frame
        caption_frame.word_wrap = True
        caption_run = caption_frame.paragraphs[0].add_run()
        caption_run.text = slide_plan.visual_brief[:120]
        caption_run.font.size = Pt(10)
        caption_run.font.color.rgb = RGBColor(31, 41, 55)
        return True

    def _select_image_url(self, evidence_orbs: list[str], context_map: dict[str, RetrievalResult]) -> str | None:
        for orb in evidence_orbs:
            item = context_map.get(orb)
            if not item:
                continue
            metadata_url = item.metadata.get("image_url")
            if isinstance(metadata_url, str) and metadata_url.startswith(("http://", "https://")):
                return metadata_url
            content_url = self._extract_first_image_url(item.content)
            if content_url:
                return content_url
        return None

    @staticmethod
    def _download_image(url: str) -> bytes | None:
        try:
            response = httpx.get(url, timeout=20.0, follow_redirects=True)
            response.raise_for_status()
        except Exception:
            return None

        content_type = response.headers.get("content-type", "").lower()
        if not content_type.startswith("image/"):
            return None
        if "webp" in content_type or "svg" in content_type:
            return None
        return response.content

    @staticmethod
    def _extract_first_image_url(content: str) -> str | None:
        matches = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", content)
        for match in matches:
            cleaned = match.strip().strip("<>").strip()
            if cleaned.startswith(("http://", "https://")) and "base64-image-removed" not in cleaned.lower():
                return cleaned
        return None

    @staticmethod
    def _orb_id(item: RetrievalResult) -> str:
        return f"ORB-{item.id[-8:]}"

    @staticmethod
    def _slugify(value: str) -> str:
        cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
        return cleaned[:80] or "presentation"
