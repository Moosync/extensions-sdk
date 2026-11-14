from dataclasses import dataclass
import extism

@dataclass
class PlatformInfo:
    os: str
    arch: str

def get_platform() -> PlatformInfo:
    try:
        os_val = extism.get_config("os")
    except Exception:
        os_val = None
    try:
        arch_val = extism.get_config("arch")
    except Exception:
        arch_val = None
    return PlatformInfo(
        os=os_val or "unknown",
        arch=arch_val or "unknown",
    )
