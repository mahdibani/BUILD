# Build

Build-Slides is an autonomous, multi-agent presentation agency. It does more than turn text into slides. It researches, reasons, designs, and stress-tests a presentation based on your specific intent.

Whether you are pitching to investors, explaining an API, or defending a thesis, Build assembles the right specialist mindset for the job and helps you prepare for the Q&A that comes after the deck.

## Architecture Overview

The system follows a multimodal research and reasoning pipeline with four distinct phases:

![Build architecture diagram](assets/build-arch.png)

### 1. Intake & Intent Classification

The pipeline begins by identifying the intent behind the presentation. This step shapes the entire downstream strategy.

- If resources are provided, the system parses and studies them directly.
- If resources are missing, the system creates a search directive to gather domain-specific evidence.

This intake layer acts as the decision point for how research should happen and which specialist should eventually take the lead.

### 2. Sensory Ingestion

Build gathers information from multiple modalities and converts them into a shared memory layer.

- `The Scout` uses Firecrawl for deep, intent-aware web research.
- `The Librarians` parse PDFs, YouTube transcripts, and audio files.
- `Gemini Embedding 2` processes text, visuals, and media signals into a unified multimodal vector store called `Core Memory`.

This gives the system a common retrieval layer that supports reasoning across documents, websites, audio, and visual content.

### 3. Specialized Reasoning

Once intent is identified, Build activates the right expert to shape the presentation:

- `The Strategist` for business decks, ROI framing, market context, and value propositions.
- `The Architect` for technical presentations, system design, specs, and implementation logic.
- `The Scholar` for academic work, citations, data integrity, and methodology.
- `The Storyteller` for creative presentations, narrative arcs, hooks, and visual impact.

These agents do not just summarize source material. They interpret it through the lens of audience, purpose, and presentation style.

### 4. Production & Stress Testing

After reasoning is complete, Build moves into delivery and preparation.

- `The Producer` programmatically generates the final `.pptx` presentation.
- `The Challenger` reviews the core memory for important material that did not make it into the slides and turns those gaps into a mock Q&A experience.

The result is not just a slide deck, but a presentation workflow that also prepares the speaker for real audience pressure.

## Pipeline Logic

At a high level, the flow looks like this:

1. The user provides a topic and optional files.
2. The system classifies the presentation intent.
3. Build either parses provided resources or launches targeted research.
4. All multimodal inputs are embedded into shared core memory.
5. A specialist agent is selected based on the presentation context.
6. The slide deck is generated from that specialist's reasoning.
7. The Challenger produces a mock Q&A session from uncovered knowledge gaps.

## Key Features

- `Native Multimodal RAG`: Agents can reason across text, visuals, transcripts, and audio from a shared retrieval layer.
- `Intent-Driven Research`: Research strategy changes based on audience and goal, not just topic keywords.
- `Specialist Agents`: Different presentation types trigger different reasoning behaviors.
- `Automated Deck Production`: Output is a generated `.pptx`, not just notes or bullet points.
- `Stress-Tested Delivery`: The Challenger helps users rehearse difficult questions before the real presentation.

## Why Build

Most slide tools help you format content. Build helps you think, structure, and defend it.

It is designed for presentations where the stakes are higher than aesthetics alone: investor pitches, technical architecture reviews, academic defenses, and narrative-driven talks that need both substance and polish.
