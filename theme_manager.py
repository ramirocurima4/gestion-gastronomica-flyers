"""
Re-exportación directa de ThemeManager desde views/theme_manager.py.
Permite importar `from theme_manager import ThemeManager` cómodamente en todo el proyecto.
"""

from views.theme_manager import ThemeManager

__all__ = ["ThemeManager"]
