"""
Reconstrução de Imagens de Tomografia Computadorizada
Com Editor Interativo de Fantomas Personalizados
Modelos: FBP (Retroprojeção Filtrada) e IR (Iterative Reconstruction - SART)
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Circle, Rectangle
from matplotlib.widgets import Button, RadioButtons
from skimage.data import shepp_logan_phantom
from skimage.transform import radon, iradon, iradon_sart, rescale
import time 

# ==============================
#        EDITOR DE FANTOMA
# ==============================

class EditorFantoma:
    """Editor interativo para criar fantomas personalizados"""
    
    def __init__(self, tamanho=256):
        self.tamanho = tamanho
        self.fantoma = np.zeros((tamanho, tamanho))
        self.formas = []
        
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
        
        self.ax_editor.set_xlim(0, tamanho)
        self.ax_editor.set_ylim(0, tamanho)
        self.ax_editor.set_aspect('equal')
        self.ax_editor.set_title('Clique para adicionar formas')
        self.ax_editor.grid(True, alpha=0.3)
        
        self.im = self.ax_preview.imshow(self.fantoma, cmap='gray', vmin=0, vmax=1)
        self.ax_preview.set_title('Preview do Fantoma')
        self.ax_preview.axis('off')
        
        self.ax_legenda.axis('off')
        self.atualizar_legenda()
        
        # Botões
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
        
        # Radio buttons de material (aumentei a altura da caixa em y)
        ax_radio = plt.axes([0.42, 0.01, 0.40, 0.12])
        ax_radio.set_title('Material:', fontweight='bold', loc='left')
        self.radio = RadioButtons(ax_radio, list(self.materiais.keys()), active=2)
        self.radio.on_clicked(self.set_material)
        
        self.modo = 'circle'
        self.cliques = []
        self.concluido = False
        
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
    
    def set_mode(self, modo):
        self.modo = modo
        self.cliques = []
        print(f"Modo: {modo.upper()} | Material: {self.material_atual}")
    
    def set_material(self, label):
        self.material_atual = label
        self.atualizar_legenda()
    
    def atualizar_legenda(self):
        self.ax_legenda.clear()
        self.ax_legenda.axis('off')
        self.ax_legenda.text(0.5, 1.0, 'Materiais', ha='center', fontweight='bold')
        for i, (mat, info) in enumerate(self.materiais.items()):
            y = 0.9 - i * 0.12
            self.ax_legenda.add_patch(Rectangle((0.1, y - 0.03), 0.1, 0.06, facecolor=info['cor']))
            self.ax_legenda.text(0.25, y, f"{mat}\n{info['valor']} HU", va='center', fontsize=8)
        self.fig.canvas.draw()
    
    def on_click(self, event):
        if event.inaxes != self.ax_editor:
            return
        x, y = event.xdata, event.ydata
        self.cliques.append((x, y))
        self.ax_editor.plot(x, y, 'r+', markersize=10)
        if len(self.cliques) == 2:
            self.adicionar_forma()
            self.cliques = []
        self.fig.canvas.draw()
    
    def adicionar_forma(self):
        x1, y1 = self.cliques[0]
        x2, y2 = self.cliques[1]
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        width, height = abs(x2 - x1), abs(y2 - y1)
        material_info = self.materiais[self.material_atual]
        intensidade = material_info['intensidade']
        cor = material_info['cor']
        
        if self.modo == 'circle':
            raio = np.sqrt(width**2 + height**2) / 2
            patch = Circle((cx, cy), raio, fill=False, edgecolor=cor, linewidth=2)
            forma = ('circle', (cx, cy, raio), intensidade)
        elif self.modo == 'ellipse':
            patch = Ellipse((cx, cy), width, height, fill=False, edgecolor=cor, linewidth=2)
            forma = ('ellipse', (cx, cy, width, height), intensidade)
        else:
            patch = Rectangle((x1, y1), width, height, fill=False, edgecolor=cor, linewidth=2)
            forma = ('rectangle', (cx, cy, width, height), intensidade)
        
        self.formas.append(forma)
        self.ax_editor.add_patch(patch)
        self.atualizar_fantoma()
    
    def atualizar_fantoma(self):
        f = np.zeros((self.tamanho, self.tamanho))
        y, x = np.ogrid[:self.tamanho, :self.tamanho]
        for tipo, params, val in self.formas:
            if tipo == 'circle':
                cx, cy, r = params
                mask = (x - cx)**2 + (y - cy)**2 <= r**2
            elif tipo == 'ellipse':
                cx, cy, w, h = params
                mask = ((x - cx) / (w / 2))**2 + ((y - cy) / (h / 2))**2 <= 1
            else:
                cx, cy, w, h = params
                mask = (np.abs(x - cx) <= w / 2) & (np.abs(y - cy) <= h / 2)
            f[mask] = val
        self.fantoma = f
        self.im.set_data(self.fantoma)
        self.fig.canvas.draw()
    
    def limpar(self):
        self.formas = []
        self.fantoma = np.zeros((self.tamanho, self.tamanho))
        self.ax_editor.clear()
        self.ax_editor.set_xlim(0, self.tamanho)
        self.ax_editor.set_ylim(0, self.tamanho)
        self.ax_editor.grid(True, alpha=0.3)
        self.fig.canvas.draw()
    
    def concluir(self):
        self.concluido = True
        plt.close(self.fig)
    
    def mostrar(self):
        plt.show()
        return self.fantoma if self.concluido else None


# ==============================
#     MÉTODOS DE RECONSTRUÇÃO
# ==============================

def simular_projecoes(imagem, num_angulos=180, ruido=1.0):
    angulos = np.linspace(0, 180, num_angulos, endpoint=False)
    sinograma = radon(imagem, theta=angulos, circle=True)
    if ruido > 0:
        sinograma += ruido * np.random.randn(*sinograma.shape)
    return sinograma, angulos




def reconstruir_fbp(sinograma, angulos, filtro='ramp'):
    return iradon(sinograma, theta=angulos, filter_name=filtro, circle=True)


def reconstruir_ir(sinograma, angulos, iteracoes=10):
    recon = np.zeros_like(iradon(sinograma, theta=angulos, circle=True))
    for i in range(iteracoes):
        recon = iradon_sart(sinograma, theta=angulos, image=recon)
    return recon


def calcular_erro(orig, rec):
    orig_n = (orig - orig.min()) / (orig.max() - orig.min() + 1e-10)
    rec_n = (rec - rec.min()) / (rec.max() - rec.min() + 1e-10)
    mse = np.mean((orig_n - rec_n)**2)
    psnr = 10 * np.log10(1.0 / mse)
    return mse, psnr


# ==============================
#         TESTE COMPLETO
# ==============================


def testar_fantoma(fantoma, num_angulos=180):
    sinograma, angulos = simular_projecoes(fantoma, num_angulos)

    # --- Tempo do FBP ---
    inicio_fbp = time.time()
    rec_fbp = reconstruir_fbp(sinograma, angulos)
    tempo_fbp = time.time() - inicio_fbp

    # --- Tempo do IR (SART) ---
    inicio_ir = time.time()
    rec_ir = reconstruir_ir(sinograma, angulos)
    tempo_ir = time.time() - inicio_ir

    # --- Métricas de erro ---
    mse_fbp, psnr_fbp = calcular_erro(fantoma, rec_fbp)
    mse_ir, psnr_ir = calcular_erro(fantoma, rec_ir)

    # --- Exibição dos resultados ---
    fig, ax = plt.subplots(2, 2, figsize=(11, 8))
    ax[0, 0].imshow(fantoma, cmap='gray')
    ax[0, 0].set_title("Fantoma Original")
    ax[0, 0].axis('off')

    # Sinograma compacto + número de ângulos
    ax[0, 1].imshow(sinograma, cmap='gray', aspect=0.3)
    ax[0, 1].set_title(f"Sinograma ({num_angulos} ângulos de captura)")
    ax[0, 1].set_xlabel("Ângulo (°)")
    ax[0, 1].set_ylabel("Detectores")

    ax[1, 0].imshow(rec_fbp, cmap='gray')
    ax[1, 0].set_title(f"FBP - PSNR: {psnr_fbp:.2f} dB\nTempo: {tempo_fbp:.3f} s")
    ax[1, 0].axis('off')

    ax[1, 1].imshow(rec_ir, cmap='gray')
    ax[1, 1].set_title(f"IR (SART) - PSNR: {psnr_ir:.2f} dB\nTempo: {tempo_ir:.3f} s")
    ax[1, 1].axis('off')

    # Aumentar o espaço entre os plots
    plt.subplots_adjust(wspace=0.4, hspace=0.35)

    plt.show()

    # --- Impressão no terminal ---
    print("\nResultados:")
    print(f"FBP  -> MSE={mse_fbp:.6f}, PSNR={psnr_fbp:.2f} dB, Tempo={tempo_fbp:.3f} s")
    print(f"IR   -> MSE={mse_ir:.6f}, PSNR={psnr_ir:.2f} dB, Tempo={tempo_ir:.3f} s")




# ==============================
#        EXECUÇÃO PRINCIPAL
# ==============================

if __name__ == "__main__":
    print("\nReconstrução de TC - FBP e IR (SART)")
    print("1 - Shepp-Logan padrão")
    print("2 - Fantoma personalizado (editor interativo)")
    opcao = input("Escolha: ")

    tamanho = 256
    if opcao == "1":
        f = rescale(shepp_logan_phantom(), scale=tamanho/400, mode='reflect', channel_axis=None)
    else:
        editor = EditorFantoma(tamanho)
        f = editor.mostrar()
        if f is None or f.max() == 0:
            print("Fantoma vazio. Encerrando.")
            exit()
    
    testar_fantoma(f, num_angulos=180)
