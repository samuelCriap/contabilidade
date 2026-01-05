"""
Gerenciador de Tema - Sistema de Honorários Contábeis
Dark/Light mode com cores dinâmicas
"""

# Design System - Cores
CORES = {
    # Accent colors
    "accent": "#3B82F6",
    "accent_hover": "#2563EB",
    "success": "#10B981",
    "success_hover": "#059669",
    "warning": "#F59E0B",
    "warning_hover": "#D97706",
    "danger": "#EF4444",
    "danger_hover": "#DC2626",
    "purple": "#8B5CF6",
    "indigo": "#6366F1",
    
    # Light mode - Contraste melhorado
    "bg_light": "#E2E8F0",  # Fundo cinza mais escuro
    "surface_light": "#FFFFFF",  # Cards brancos
    "surface_hover_light": "#F1F5F9",  # Hover cinza claro
    "text_primary_light": "#0F172A",  # Texto preto forte
    "text_secondary_light": "#334155",  # Texto secundário MUITO mais escuro para legibilidade
    "border_light": "#94A3B8",  # Borda bem mais visível no modo claro
    "card_shadow_light": "0.15",  # Sombra mais visível
    "input_bg_light": "#F8FAFC",  # Fundo claro para inputs
    "input_border_light": "#64748B",  # Borda visível para inputs
    
    # Dark mode
    "bg_dark": "#0F172A",
    "surface_dark": "#1E293B",
    "surface_hover_dark": "#334155",
    "text_primary_dark": "#F8FAFC",
    "text_secondary_dark": "#94A3B8",
    "border_dark": "#334155",  # Borda sutil no modo escuro
}

# Gradiente do menu lateral - Azul escuro, branco e dourado
MENU_GRADIENT_COLORS = ["#C4A962", "#B8976F", "#1A2957", "#152042", "#0F172A"]


from database import get_config, set_config

class ThemeManager:
    """Gerenciador de tema claro/escuro com persistência"""
    
    def __init__(self, dark_mode: bool = None):
        if dark_mode is not None:
            self.is_dark = [dark_mode]
        else:
            # Carregar do banco (padrão Dark se não existir)
            saved_theme = get_config("theme_mode", "dark")
            self.is_dark = [saved_theme == "dark"]
    
    def toggle(self):
        """Alterna entre dark e light mode"""
        self.is_dark[0] = not self.is_dark[0]
        self.save()
        
    def set_dark(self, dark: bool):
        """Define modo escuro"""
        self.is_dark[0] = dark
        self.save()
        
    def save(self):
        """Salva preferência no banco"""
        mode = "dark" if self.is_dark[0] else "light"
        set_config("theme_mode", mode)
    
    def get_bg(self) -> str:
        """Cor de fundo principal"""
        return CORES["bg_dark"] if self.is_dark[0] else CORES["bg_light"]
    
    def get_surface(self) -> str:
        """Cor de superfície (cards, modais)"""
        return CORES["surface_dark"] if self.is_dark[0] else CORES["surface_light"]
    
    def get_surface_hover(self) -> str:
        """Cor de superfície no hover"""
        return CORES["surface_hover_dark"] if self.is_dark[0] else CORES["surface_hover_light"]
    
    def get_text_color(self) -> str:
        """Cor do texto principal"""
        return CORES["text_primary_dark"] if self.is_dark[0] else CORES["text_primary_light"]
    
    def get_text_secondary(self) -> str:
        """Cor do texto secundário"""
        return CORES["text_secondary_dark"] if self.is_dark[0] else CORES["text_secondary_light"]
    
    def get_border(self) -> str:
        """Cor da borda de cards"""
        return CORES["border_dark"] if self.is_dark[0] else CORES["border_light"]
    
    def get_shadow_opacity(self) -> float:
        """Opacidade da sombra (mais visível no modo claro)"""
        return 0.05 if self.is_dark[0] else 0.15
    
    def get_input_bg(self) -> str:
        """Cor de fundo dos inputs"""
        return CORES["surface_hover_dark"] if self.is_dark[0] else CORES["input_bg_light"]
    
    def get_input_border(self) -> str:
        """Cor da borda dos inputs"""
        return CORES["border_dark"] if self.is_dark[0] else CORES["input_border_light"]
