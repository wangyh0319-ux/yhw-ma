from pathlib import Path

from app.services.mixing.ai_report import write_mix_report
from app.services.mixing.clipping import measure_clipping
from app.services.mixing.dynamics import measure_dynamics
from app.services.mixing.frequency import measure_frequency
from app.services.mixing.loader import load_mix_audio
from app.services.mixing.loudness import measure_loudness
from app.services.mixing.scoring import score_mix
from app.services.mixing.stereo import measure_stereo


def analyze_mix(path: Path) -> dict:
    samples, sr = load_mix_audio(path)
    analysis = {
        "duration_sec": round(samples.shape[0] / sr, 3),
        "sample_rate": sr,
        "channels": int(samples.shape[1]),
        "loudness": measure_loudness(samples, sr),
        "frequency": measure_frequency(samples, sr),
        "dynamics": measure_dynamics(samples, sr),
        "stereo": measure_stereo(samples, sr),
        "clipping": measure_clipping(samples, sr),
    }
    analysis["scores"] = score_mix(analysis)
    analysis["ai_report"] = write_mix_report(analysis)
    return analysis
