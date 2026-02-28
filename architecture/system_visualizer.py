from __future__ import annotations

from pathlib import Path

from architecture.architecture_graph_generator import ArchitectureGraphGenerator


class SystemVisualizer:
    def render(self, output_dir: str | Path) -> Path:
        graph = ArchitectureGraphGenerator().build()
        output_path = Path(output_dir) / "AGI_1_COGNITIVE_ARCHITECTURE.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            "# AGI-1 Cognitive Architecture\n\n```mermaid\n"
            + graph["mermaid"]
            + "\n```\n",
            encoding="utf-8",
        )
        return output_path
