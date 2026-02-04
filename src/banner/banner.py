"""Create Banner."""
from rich.console import Console
from rich.text import Text


def get_version(version):
    """
    Display professional banner with version.

    :param version: Version string
    :return: Version string
    """
    console = Console()
    
    # Create the banner with a clean, modern design
    banner_lines = [
        "",
        "╔═══════════════════════════════════════════════════════════════╗",
        "║                                                               ║",
        "║              🔄  REVERSE DIAGRAMS                             ║",
        "║                                                               ║",
        "║        AWS Infrastructure Documentation as Code               ║",
        "║                                                               ║",
        "╚═══════════════════════════════════════════════════════════════╝",
        ""
    ]
    
    # Print banner with colors
    for line in banner_lines:
        if "REVERSE DIAGRAMS" in line:
            text = Text(line, style="bold cyan")
        elif "AWS Infrastructure" in line:
            text = Text(line, style="green")
        elif "═" in line or "║" in line:
            text = Text(line, style="cyan")
        else:
            text = Text(line)
        console.print(text, justify="center")
    
    # Print version info
    version_text = Text()
    version_text.append("  Version ", style="dim")
    version_text.append(version, style="bold yellow")
    version_text.append("  •  ", style="dim")
    version_text.append("github.com/velez94/reverse_diagrams", style="dim cyan underline")
    version_text.append("  ", style="dim")
    
    console.print(version_text, justify="center")
    console.print()
    
    return version
