"""
Paquete de vistas e interfaz gráfica de usuario construida con CustomTkinter.
"""

from views.app_ui import AppUI
from views.tab_caja import TabCaja
from views.tab_flyer import TabFlyer
from views.tab_menu import TabMenu

__all__ = ["AppUI", "TabMenu", "TabFlyer", "TabCaja"]
