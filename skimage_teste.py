"""
Reconstrução de Imagens de Tomografia Computadorizada
Com Editor Interativo de Fantomas Personalizados
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Circle, Rectangle, Polygon
from matplotlib.widgets import Button, TextBox, RadioButtons, RadioButtons
from skimage.data import shepp_logan_phantom
from skimage.transform import radon, iradon, rescale
from scipy.fft import fft, ifft, fftfreq

# Configurações
np.random.seed(42)

class EditorFantoma:
    """Editor interativo para criar fantomas personalizados"""
    
    def __init__(self, tamanho=256):
        self.tamanho = tamanho
        self.fantoma = np.zeros((tamanho, tamanho))
        self.formas = []
        
        # Materiais com valores de atenuação em Unidades Hounsfield (HU)
        # Normalizados para 0-1 para visualização
        self.materiais = {
            'Ar/Pulmão': {'valor': -1000, 'cor': 'black', 'intensidade': 0.0},
            'Gordura': {'valor': -100, 'cor': 'darkgray', 'intensidade': 0.2},
            'Água/Tecido Mole': {'valor': 0, 'cor': 'gray', 'intensidade': 0.5},
            'Músculo': {'valor': 50, 'cor': 'lightcoral', 'intensidade': 0.6},
            'Sangue': {'valor': 40, 'cor': 'red', 'intensidade': 0.65},
            'Osso Esponjoso': {'valor': 400, 'cor': 'wheat', 'intensidade': 0.8},
            'Osso Cortical': {'valor': 1000, 'cor': 'white', 'intensidade': 1.0},
        }
        
        self.material_atual = 'Água/Tecido Mole'
        
        # Configurar figura
        self.fig = plt.figure(figsize=(16, 7))
        gs = self.fig.add_gridspec(2, 3, width_ratios=[2, 2, 1], height_ratios=[10, 1])
        
        self.ax_editor = self.fig.add_subplot(gs[0, 0])
        self.ax_preview = self.fig.add_subplot(gs[0, 1])
        self.ax_legenda = self.fig.add_subplot(gs[0, 2])
        
        self.fig.suptitle('Editor de Fantoma Personalizado - TC com Materiais', 
                         fontsize=14, fontweight='bold')
        
        # Configurar eixos
        self.ax_editor.set_xlim(0, tamanho)
        self.ax_editor.set_ylim(0, tamanho)
        self.ax_editor.set_aspect('equal')
        self.ax_editor.set_title('Clique para adicionar formas')
        self.ax_editor.grid(True, alpha=0.3)
        
        self.im = self.ax_preview.imshow(self.fantoma, cmap='gray', vmin=0, vmax=1)
        self.ax_preview.set_title('Preview do Fantoma')
        self.ax_preview.axis('off')
        
        # Legenda de materiais
        self.ax_legenda.axis('off')
        self.atualizar_legenda()
        
        # Botões de formas
        ax_btn_circle = plt.axes([0.12, 0.02, 0.06, 0.04])
        ax_btn_ellipse = plt.axes([0.19, 0.02, 0.06, 0.04])
        ax_btn_rect = plt.axes([0.26, 0.02, 0.06, 0.04])
        ax_btn_clear = plt.axes([0.33, 0.02, 0.06, 0.04])
        ax_btn_done = plt.axes([0.85, 0.02, 0.06, 0.04])
        
        self.btn_circle = Button(ax_btn_circle, 'Círculo')
        self.btn_ellipse = Button(ax_btn_ellipse, 'Elipse')
        self.btn_rect = Button(ax_btn_rect, 'Retângulo')
        self.btn_clear = Button(ax_btn_clear, 'Limpar')
        self.btn_done = Button(ax_btn_done, 'Concluir')
        
        self.btn_circle.on_clicked(lambda x: self.set_mode('circle'))
        self.btn_ellipse.on_clicked(lambda x: self.set_mode('ellipse'))
        self.btn_rect.on_clicked(lambda x: self.set_mode('rectangle'))
        self.btn_clear.on_clicked(lambda x: self.limpar())
        self.btn_done.on_clicked(lambda x: self.concluir())
        
        # Radio buttons para materiais
        ax_radio = plt.axes([0.42, 0.01, 0.40, 0.06])
        ax_radio.set_title('Material:', fontweight='bold', loc='left')
        self.radio = RadioButtons(ax_radio, list(self.materiais.keys()), active=2)
        self.radio.on_clicked(self.set_material)
        
        self.modo = 'circle'
        self.cliques = []
        self.concluido = False
        
        # Conectar eventos
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        
        print("\n" + "="*60)
        print("EDITOR DE FANTOMA INTERATIVO COM MATERIAIS")
        print("="*60)
        print("Instruções:")
        print("1. Selecione um MATERIAL (Ar, Tecido, Osso, etc.)")
        print("2. Selecione uma FORMA (Círculo, Elipse ou Retângulo)")
        print("3. Clique 2 vezes no editor para definir a forma")
        print("4. Repita para adicionar mais formas com diferentes materiais")
        print("5. Clique em 'Concluir' quando terminar")
        print("\n💡 Valores em Unidades Hounsfield (HU):")
        for mat, info in self.materiais.items():
            print(f"   {mat:20s}: {info['valor']:5d} HU")
        print("="*60 + "\n")
    
    def set_mode(self, modo):
        self.modo = modo
        self.cliques = []
        print(f"Modo: {modo.upper()} | Material: {self.material_atual} - Clique 2 vezes")
    
    def set_material(self, label):
        self.material_atual = label
        print(f"Material selecionado: {label} ({self.materiais[label]['valor']} HU)")
        self.atualizar_legenda()
    
    def atualizar_legenda(self):
        """Atualiza a legenda de materiais com destaque no material atual"""
        self.ax_legenda.clear()
        self.ax_legenda.axis('off')
        self.ax_legenda.set_xlim(0, 1)
        self.ax_legenda.set_ylim(0, len(self.materiais) + 1)
        
        self.ax_legenda.text(0.5, len(self.materiais) + 0.5, 'MATERIAIS', 
                            ha='center', fontweight='bold', fontsize=11)
        
        for i, (mat, info) in enumerate(reversed(list(self.materiais.items()))):
            y = i + 0.5
            
            # Destaque para material atual
            if mat == self.material_atual:
                self.ax_legenda.add_patch(Rectangle((0, y-0.4), 1, 0.8, 
                                                    facecolor='yellow', alpha=0.3))
            
            # Quadrado colorido
            self.ax_legenda.add_patch(Rectangle((0.05, y-0.25), 0.15, 0.5, 
                                                facecolor=info['cor'], edgecolor='black'))
            
            # Texto
            self.ax_legenda.text(0.25, y, f"{mat}\n{info['valor']} HU", 
                               va='center', fontsize=8)
        
        self.fig.canvas.draw()
    
    def on_click(self, event):
        if event.inaxes != self.ax_editor:
            return
        
        x, y = event.xdata, event.ydata
        self.cliques.append((x, y))
        
        # Desenhar ponto temporário
        self.ax_editor.plot(x, y, 'r+', markersize=10)
        self.fig.canvas.draw()
        
        if len(self.cliques) == 2:
            self.adicionar_forma()
            self.cliques = []
    
    def adicionar_forma(self):
        x1, y1 = self.cliques[0]
        x2, y2 = self.cliques[1]
        
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        
        material_info = self.materiais[self.material_atual]
        intensidade = material_info['intensidade']
        cor = material_info['cor']
        
        if self.modo == 'circle':
            raio = np.sqrt(width**2 + height**2) / 2
            forma = {
                'tipo': 'circle', 
                'centro': (cx, cy), 
                'raio': raio, 
                'intensidade': intensidade,
                'material': self.material_atual,
                'valor_hu': material_info['valor']
            }
            patch = Circle((cx, cy), raio, fill=False, edgecolor=cor, linewidth=2.5, linestyle='--')
        
        elif self.modo == 'ellipse':
            forma = {
                'tipo': 'ellipse', 
                'centro': (cx, cy), 
                'width': width, 
                'height': height, 
                'intensidade': intensidade,
                'material': self.material_atual,
                'valor_hu': material_info['valor']
            }
            patch = Ellipse((cx, cy), width, height, fill=False, edgecolor=cor, linewidth=2.5, linestyle='--')
        
        elif self.modo == 'rectangle':
            forma = {
                'tipo': 'rectangle', 
                'centro': (cx, cy), 
                'width': width, 
                'height': height, 
                'intensidade': intensidade,
                'material': self.material_atual,
                'valor_hu': material_info['valor']
            }
            patch = Rectangle((x1, y1), width, height, fill=False, edgecolor=cor, linewidth=2.5, linestyle='--')
        
        self.formas.append(forma)
        self.ax_editor.add_patch(patch)
        self.atualizar_fantoma()
        self.fig.canvas.draw()
        
        print(f"✓ {self.modo.capitalize()} de {self.material_atual} adicionado em ({cx:.1f}, {cy:.1f})")
    
    def atualizar_fantoma(self):
        self.fantoma = np.zeros((self.tamanho, self.tamanho))
        
        y, x = np.ogrid[:self.tamanho, :self.tamanho]
        
        for forma in self.formas:
            cx, cy = forma['centro']
            intensidade = forma['intensidade']
            
            if forma['tipo'] == 'circle':
                raio = forma['raio']
                mascara = (x - cx)**2 + (y - cy)**2 <= raio**2
            
            elif forma['tipo'] == 'ellipse':
                w = forma['width'] / 2
                h = forma['height'] / 2
                mascara = ((x - cx) / w)**2 + ((y - cy) / h)**2 <= 1
            
            elif forma['tipo'] == 'rectangle':
                w = forma['width'] / 2
                h = forma['height'] / 2
                mascara = (np.abs(x - cx) <= w) & (np.abs(y - cy) <= h)
            
            self.fantoma[mascara] = intensidade
        
        self.im.set_data(self.fantoma)
        self.ax_preview.set_title(f'Preview ({len(self.formas)} formas)')
    
    def limpar(self):
        self.formas = []
        self.fantoma = np.zeros((self.tamanho, self.tamanho))
        self.ax_editor.clear()
        self.ax_editor.set_xlim(0, self.tamanho)
        self.ax_editor.set_ylim(0, self.tamanho)
        self.ax_editor.set_aspect('equal')
        self.ax_editor.set_title('Clique para adicionar formas')
        self.ax_editor.grid(True, alpha=0.3)
        self.atualizar_fantoma()
        self.fig.canvas.draw()
        print("Editor limpo!")
    
    def concluir(self):
        self.concluido = True
        plt.close(self.fig)
        print(f"\n✓ Fantoma criado com {len(self.formas)} formas!")
        print("\n📋 Resumo dos materiais:")
        materiais_usados = {}
        for forma in self.formas:
            mat = forma['material']
            materiais_usados[mat] = materiais_usados.get(mat, 0) + 1
        for mat, count in materiais_usados.items():
            print(f"   {mat}: {count} forma(s)")
    
    def mostrar(self):
        plt.show()
        return self.fantoma if self.concluido else None


def criar_fantoma_shepp_logan(tamanho=256):
    """Cria o fantoma de Shepp-Logan padrão"""
    fantoma = shepp_logan_phantom()
    fantoma = rescale(fantoma, scale=tamanho/400, mode='reflect', channel_axis=None)
    return fantoma


def criar_fantoma_personalizado(tamanho=256):
    """Abre o editor interativo para criar um fantoma"""
    editor = EditorFantoma(tamanho)
    fantoma = editor.mostrar()
    return fantoma if fantoma is not None else np.zeros((tamanho, tamanho))


def criar_fantoma_predefinido(tipo='simple', tamanho=256):
    """
    Cria fantomas predefinidos simples
    
    Tipos disponíveis:
    - 'simple': Círculo central
    - 'double': Dois círculos
    - 'cross': Cruz
    - 'squares': Quadrados
    """
    fantoma = np.zeros((tamanho, tamanho))
    y, x = np.ogrid[:tamanho, :tamanho]
    cy, cx = tamanho // 2, tamanho // 2
    
    if tipo == 'simple':
        # Círculo central grande
        mascara = (x - cx)**2 + (y - cy)**2 <= (tamanho // 3)**2
        fantoma[mascara] = 1.0
        
        # Círculo interno menor
        mascara = (x - cx)**2 + (y - cy)**2 <= (tamanho // 6)**2
        fantoma[mascara] = 0.5
    
    elif tipo == 'double':
        # Dois círculos
        r = tamanho // 4
        mascara1 = (x - cx + r)**2 + (y - cy)**2 <= r**2
        mascara2 = (x - cx - r)**2 + (y - cy)**2 <= r**2
        fantoma[mascara1] = 0.8
        fantoma[mascara2] = 0.6
    
    elif tipo == 'cross':
        # Cruz
        w = tamanho // 8
        mascara_h = np.abs(y - cy) <= w
        mascara_v = np.abs(x - cx) <= w
        fantoma[mascara_h | mascara_v] = 0.7
    
    elif tipo == 'squares':
        # Quadrados
        s = tamanho // 4
        for i in [-1, 1]:
            for j in [-1, 1]:
                x1, x2 = cx + i * s // 2 - s // 4, cx + i * s // 2 + s // 4
                y1, y2 = cy + j * s // 2 - s // 4, cy + j * s // 2 + s // 4
                fantoma[y1:y2, x1:x2] = 0.5 + 0.2 * (i + j)
    
    return fantoma


def simular_projecoes(imagem, num_angulos=180, ruido=0.0):
    """Simula projeções de tomografia (sinograma)"""
    angulos = np.linspace(0, 180, num_angulos, endpoint=False)
    sinograma = radon(imagem, theta=angulos, circle=True)
    
    if ruido > 0:
        sinograma += ruido * np.random.randn(*sinograma.shape)
    
    return sinograma, angulos


def retroprojecao_filtrada(sinograma, angulos, filtro='ramp'):
    """Reconstrução por retroprojeção filtrada (FBP)"""
    return iradon(sinograma, theta=angulos, filter_name=filtro, circle=True)


def calcular_erro(original, reconstruida):
    """Calcula métricas de erro"""
    original_norm = (original - original.min()) / (original.max() - original.min() + 1e-10)
    reconstruida_norm = (reconstruida - reconstruida.min()) / (reconstruida.max() - reconstruida.min() + 1e-10)
    
    mse = np.mean((original_norm - reconstruida_norm) ** 2)
    psnr = 10 * np.log10(1.0 / mse) if mse > 0 else float('inf')
    
    return mse, psnr


def testar_fantoma(fantoma, num_angulos=180):
    """Testa reconstrução de um fantoma"""
    if fantoma is None or fantoma.max() == 0:
        print("Erro: Fantoma vazio ou inválido!")
        return
    
    print(f"\nTestando reconstrução com {num_angulos} ângulos...")
    
    # Simular projeções
    sinograma, angulos = simular_projecoes(fantoma, num_angulos=num_angulos)
    
    # Reconstruir
    recon_ramp = retroprojecao_filtrada(sinograma, angulos, filtro='ramp')
    recon_shepp = retroprojecao_filtrada(sinograma, angulos, filtro='shepp-logan')
    
    # Calcular erros
    mse_ramp, psnr_ramp = calcular_erro(fantoma, recon_ramp)
    mse_shepp, psnr_shepp = calcular_erro(fantoma, recon_shepp)
    
    # Visualizar
    fig, axes = plt.subplots(2, 2, figsize=(12, 12))
    
    axes[0, 0].imshow(fantoma, cmap='gray')
    axes[0, 0].set_title('Fantoma Original', fontweight='bold')
    axes[0, 0].axis('off')
    
    axes[0, 1].imshow(sinograma, cmap='gray', aspect='auto')
    axes[0, 1].set_title(f'Sinograma ({num_angulos} ângulos)', fontweight='bold')
    axes[0, 1].set_xlabel('Ângulo de projeção')
    axes[0, 1].set_ylabel('Posição do detector')
    
    axes[1, 0].imshow(recon_ramp, cmap='gray')
    axes[1, 0].set_title(f'Reconstrução - Filtro Ramp\nPSNR: {psnr_ramp:.2f} dB', fontweight='bold')
    axes[1, 0].axis('off')
    
    axes[1, 1].imshow(recon_shepp, cmap='gray')
    axes[1, 1].set_title(f'Reconstrução - Filtro Shepp-Logan\nPSNR: {psnr_shepp:.2f} dB', fontweight='bold')
    axes[1, 1].axis('off')
    
    plt.suptitle('Teste de Reconstrução TC', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.show()
    
    print(f"\n📊 RESULTADOS:")
    print("=" * 60)
    print(f"Filtro Ramp:        MSE={mse_ramp:.6f}, PSNR={psnr_ramp:.2f} dB")
    print(f"Filtro Shepp-Logan: MSE={mse_shepp:.6f}, PSNR={psnr_shepp:.2f} dB")
    print("=" * 60)


def menu_principal():
    """Menu interativo para escolher tipo de fantoma"""
    print("\n" + "="*60)
    print("RECONSTRUÇÃO DE TOMOGRAFIA COMPUTADORIZADA")
    print("="*60)
    print("\nEscolha o tipo de fantoma:")
    print("1 - Shepp-Logan (padrão)")
    print("2 - Criar fantoma personalizado (editor interativo)")
    print("3 - Fantoma simples (círculo)")
    print("4 - Fantoma duplo (dois círculos)")
    print("5 - Fantoma cruz")
    print("6 - Fantoma quadrados")
    print("0 - Sair")
    print("="*60)
    
    escolha = input("\nDigite sua escolha: ")
    
    tamanho = 256
    num_angulos = 180
    
    if escolha == '1':
        print("\nCriando fantoma de Shepp-Logan...")
        fantoma = criar_fantoma_shepp_logan(tamanho)
        testar_fantoma(fantoma, num_angulos)
    
    elif escolha == '2':
        print("\nAbrindo editor de fantoma personalizado...")
        fantoma = criar_fantoma_personalizado(tamanho)
        if fantoma is not None and fantoma.max() > 0:
            testar_fantoma(fantoma, num_angulos)
    
    elif escolha == '3':
        print("\nCriando fantoma simples...")
        fantoma = criar_fantoma_predefinido('simple', tamanho)
        testar_fantoma(fantoma, num_angulos)
    
    elif escolha == '4':
        print("\nCriando fantoma duplo...")
        fantoma = criar_fantoma_predefinido('double', tamanho)
        testar_fantoma(fantoma, num_angulos)
    
    elif escolha == '5':
        print("\nCriando fantoma cruz...")
        fantoma = criar_fantoma_predefinido('cross', tamanho)
        testar_fantoma(fantoma, num_angulos)
    
    elif escolha == '6':
        print("\nCriando fantoma quadrados...")
        fantoma = criar_fantoma_predefinido('squares', tamanho)
        testar_fantoma(fantoma, num_angulos)
    
    elif escolha == '0':
        print("\nEncerrando programa...")
        return False
    
    else:
        print("\nOpção inválida!")
    
    return True


if __name__ == "__main__":
    continuar = True
    while continuar:
        continuar = menu_principal()
    
    print("\nPrograma finalizado!")
    print("="*60)
