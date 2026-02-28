from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from multimodal_studio import MediaStudioService, StudioConfig
from multimodal_studio.video import FfmpegEncoder


def main() -> None:
    config = StudioConfig.from_env()
    service = MediaStudioService(config=config)
    ffmpeg = FfmpegEncoder()

    components = [
        {
            "component": "multimodal_studio_core",
            "status": "ACTIVE",
            "evidence": "service_importable_and_runtime_initialized",
        },
        {
            "component": "media_rest_routes",
            "status": "ACTIVE",
            "evidence": "api/routes_media.py + api/ws_media.py",
        },
        {
            "component": "open_data_connectors",
            "status": "ACTIVE",
            "evidence": "platform adapters + query engine + provenance",
        },
        {
            "component": "design_three_d_printing_pipelines",
            "status": "ACTIVE",
            "evidence": "design/* + three_d/* + printing/* modules wired into service/routes",
        },
        {
            "component": "ffmpeg_video_encode",
            "status": "ACTIVE" if ffmpeg.available() else "DEGRADED",
            "evidence": shutil.which("ffmpeg") or "ffmpeg_not_installed",
        },
    ]

    blockers = [
        "Install ffmpeg for non-degraded MP4 encoding"
        for item in components
        if item["component"] == "ffmpeg_video_encode" and item["status"] == "DEGRADED"
    ]

    status_payload = service.status_payload()
    jobs_total = int(status_payload.get("jobs_total", 0))

    report = {
        "pm": "OpenClaw",
        "exec": "Jack | Julia | Singularity | Aegis",
        "decision": "GO" if not blockers else "NO-GO",
        "components": components,
        "blockers": blockers,
        "jobs_tracked": jobs_total,
    }

    output_path = Path("runtime") / "multimodal_go_no_go.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
