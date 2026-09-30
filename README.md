# snake: IA que aprende a jogar sozinha

Snake em Pygame controlado por uma rede neural treinada com **neuroevolução** (algoritmo genético), só com NumPy: sem dataset, sem backprop e sem PyTorch.

## Como funciona
- **Estado (11 entradas, 0/1):** perigo à frente, à direita e à esquerda; direção atual (one-hot); posição da comida em relação à cabeça. Como é relativo, funciona em qualquer tamanho de tabuleiro.
- **Rede:** 11 → 16 → 12 → 3 (ReLU), 435 parâmetros. Saídas: seguir reto, virar à direita, virar à esquerda.
- **Evolução:** 150 indivíduos por geração, elitismo (10%), torneio, crossover uniforme e mutação gaussiana.
- **Fitness:** comida (com bônus quadrático), aproximação da comida e morte por fome para evitar loops.

## Estrutura
| Arquivo | O que faz |
|---|---|
| `main.py` | ponto de entrada |
| `game.py`, `snake.py`, `food.py`, `config.py` | o jogo (tabuleiro 50×50) |
| `genetic_ai.py` | rede neural, algoritmo genético, ambiente de treino e painel visual |
| `train.py` | CLI de treino (retoma de onde parou) |
| `best_snake.npz` | pesos do melhor agente |
| `best_snake_state.pkl` | população completa, para continuar o treino |

## Como rodar
```bash
pip install -r requirements.txt
python train.py --generations 100   # com painel visual
python train.py --headless          # mais rápido, em paralelo
python train.py --fresh             # recomeça do zero
python main.py                      # assiste a IA jogando
```
