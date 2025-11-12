# Reconstrução de Imagens de Tomografia Computadorizada

## Sobre o Projeto

Este projeto implementa e compara dois métodos clássicos de reconstrução de imagens em Tomografia Computadorizada (TC):

- **FBP (Filtered Back Projection)**: Método analítico tradicional, rápido e direto
- **IR (Iterative Reconstruction - SART)**: Método iterativo que refina progressivamente a imagem

O projeto inclui um **editor interativo** que permite criar fantomas personalizados para testar os algoritmos de reconstrução, além de utilizar o fantoma Shepp-Logan clássico.

## Funcionalidades

### 1. Editor Interativo de Fantomas

O editor permite criar fantomas personalizados com diferentes materiais e formas geométricas:

**Materiais Disponíveis:**
- Ar/Pulmão (-1000 HU)
- Gordura (-100 HU)
- Água/Tecido Mole (0 HU)
- Músculo (50 HU)
- Sangue (40 HU)
- Osso Esponjoso (400 HU)
- Osso Cortical (1000 HU)

**Formas Geométricas:**
- Círculos
- Elipses
- Retângulos

### 2. Simulação de Aquisição

- Geração de sinogramas a partir das projeções
- Configuração do número de ângulos de captura
- Adição de ruído simulando condições reais

### 3. Reconstrução e Análise

- Reconstrução usando FBP e IR (SART)
- Medição de tempo de processamento
- Cálculo de métricas de qualidade (MSE e PSNR)
- Visualização comparativa dos resultados

## Requisitos
```bash
numpy
matplotlib
scikit-image
```

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/marlonsp/Fisica-Medica-TC.git
cd Fisica-Medica-TC
```

2. Instale as dependências:
```bash
pip install numpy matplotlib scikit-image
```

## Como Executar

### Execução Básica
```bash
python projeto_final.py
```

### Opções de Uso

Ao executar, você verá o seguinte menu:
```
Reconstrução de TC - FBP e IR (SART)
1 - Shepp-Logan padrão
2 - Fantoma personalizado (editor interativo)
Escolha:
```

#### Opção 1: Fantoma Shepp-Logan Padrão

- Digite `1` e pressione Enter
- O programa carregará automaticamente o fantoma Shepp-Logan
- As reconstruções serão exibidas automaticamente

#### Opção 2: Editor Interativo

Digite `2` e pressione Enter para abrir o editor interativo:

**Passos para criar seu fantoma:**

1. **Selecione o material** usando os botões de rádio na parte inferior
2. **Escolha a forma** clicando em um dos botões:
   - `Círculo`: para formas circulares
   - `Elipse`: para formas elípticas
   - `Retângulo`: para formas retangulares
3. **Desenhe a forma**:
   - Clique uma vez para marcar o primeiro ponto
   - Clique novamente para marcar o segundo ponto
   - A forma será criada automaticamente
4. **Repita** para adicionar mais formas
5. **Botões de controle**:
   - `Limpar`: remove todas as formas
   - `Concluir`: finaliza a edição e inicia a reconstrução

**Dica:** O preview do fantoma é atualizado em tempo real no painel direito.

## Estrutura do Código

### Classes Principais

#### `EditorFantoma`
Classe responsável pela interface interativa de criação de fantomas.

**Principais métodos:**
- `set_mode(modo)`: Define o tipo de forma a ser desenhada
- `set_material(label)`: Define o material atual
- `adicionar_forma()`: Adiciona uma forma ao fantoma
- `atualizar_fantoma()`: Atualiza a matriz do fantoma
- `limpar()`: Remove todas as formas
- `concluir()`: Finaliza a edição

### Funções de Reconstrução

#### `simular_projecoes(imagem, num_angulos, ruido)`
Simula a aquisição de projeções em um tomógrafo.

**Parâmetros:**
- `imagem`: Matriz do fantoma original
- `num_angulos`: Número de ângulos de projeção (padrão: 180)
- `ruido`: Nível de ruído a ser adicionado (padrão: 1.0)

**Retorna:** Sinograma e array de ângulos

#### `reconstruir_fbp(sinograma, angulos, filtro)`
Reconstrói a imagem usando Filtered Back Projection.

**Parâmetros:**
- `sinograma`: Dados das projeções
- `angulos`: Ângulos de aquisição
- `filtro`: Tipo de filtro ('ramp', 'shepp-logan', etc.)

#### `reconstruir_ir(sinograma, angulos, iteracoes)`
Reconstrói a imagem usando o método iterativo SART.

**Parâmetros:**
- `sinograma`: Dados das projeções
- `angulos`: Ângulos de aquisição
- `iteracoes`: Número de iterações (padrão: 10)

#### `calcular_erro(orig, rec)`
Calcula métricas de qualidade da reconstrução.

**Retorna:**
- `MSE`: Mean Squared Error
- `PSNR`: Peak Signal-to-Noise Ratio (em dB)

### Função Principal

#### `testar_fantoma(fantoma, num_angulos)`
Executa todo o pipeline de teste:
1. Gera sinograma
2. Reconstrói usando FBP e IR
3. Calcula métricas
4. Exibe resultados visuais e no terminal

## Interpretando os Resultados

### Visualização

O programa exibe uma janela com 4 painéis:

1. **Superior Esquerdo**: Fantoma original
2. **Superior Direito**: Sinograma gerado
3. **Inferior Esquerdo**: Reconstrução FBP com PSNR e tempo
4. **Inferior Direito**: Reconstrução IR (SART) com PSNR e tempo

### Métricas

**PSNR (Peak Signal-to-Noise Ratio):**
- Valores maiores = melhor qualidade
- Tipicamente entre 20-50 dB
- Acima de 30 dB indica boa qualidade

**Tempo de Processamento:**
- FBP: geralmente < 1 segundo
- IR: geralmente 3-10 segundos

**MSE (Mean Squared Error):**
- Valores menores = melhor qualidade
- Exibido no terminal

### Saída no Terminal
```
Resultados:
FBP  -> MSE=0.001234, PSNR=29.56 dB, Tempo=0.156 s
IR   -> MSE=0.000987, PSNR=30.48 dB, Tempo=5.839 s
```

## Exemplos de Uso

### Exemplo 1: Teste Rápido com Shepp-Logan
```bash
python projeto_final.py
# Digite: 1
```

### Exemplo 2: Criar um Crânio Simplificado
```bash
python projeto_final.py
# Digite: 2
# 1. Selecione "Osso Cortical"
# 2. Clique em "Círculo"
# 3. Desenhe um círculo grande (crânio externo)
# 4. Selecione "Água/Tecido Mole"
# 5. Desenhe um círculo interno (cérebro)
# 6. Clique em "Concluir"
```

## Limitações e Considerações

- O número de ângulos padrão (180) oferece boa qualidade, mas pode ser ajustado no código
- Fantomas muito complexos podem aumentar significativamente o tempo de reconstrução
- O método IR é mais lento mas geralmente produz imagens com menos ruído
- A qualidade depende do número de projeções e do nível de ruído simulado

## Referências

Para mais detalhes sobre a teoria e comparação dos métodos, consulte o relatório completo incluído no repositório (`Projeto 2 - FISMED - Entrega Final 10.11.25.pdf`).

## Autores

- Guilherme Caproni de Faria
- Marcos Vinícius
- Marlon Silva

## Repositório

GitHub: [https://github.com/marlonsp/Fisica-Medica-TC.git](https://github.com/marlonsp/Fisica-Medica-TC.git)
