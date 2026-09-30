# ai_player.py
import laya
from config import Configuration

config = Configuration()

class LayaPlayer:
    def __init__(self):
        print("Carregando Laya...")
        self.agent = laya.load("convaiinnovations/laya")
        print("Laya carregado com sucesso!")

        self.direction_map = {
            "up": 1,
            "down": 2,
            "left": 3,
            "right": 4
        }

        self.opposite = {
            1: 2,  # UP → DOWN
            2: 1,  # DOWN → UP
            3: 4,  # LEFT → RIGHT
            4: 3   # RIGHT → LEFT
        }

    def decide(self, snake, food):
        head_x, head_y = snake.body[0]
        food_x, food_y = food.position
        current_dir = snake.direction
        body = snake.body

        # Calcula o tamanho do grid
        grid_w = int(config.screen_size[0] / config.size_rect)
        grid_h = int(config.screen_size[1] / config.size_rect)

        # Converte posições de pixels para coordenadas de grid
        head_grid = (head_x // config.size_rect, head_y // config.size_rect)
        food_grid = (food_x // config.size_rect, food_y // config.size_rect)
        body_grid = [(x // config.size_rect, y // config.size_rect) for x, y in body]

        # Calcula distância e direção relativa da comida
        dx = food_grid[0] - head_grid[0]
        dy = food_grid[1] - head_grid[1]

        # Direções possíveis (sem virar 180°)
        possible_moves = []
        for name, value in self.direction_map.items():
            if value != self.opposite[current_dir]:
                possible_moves.append(name)

        # Verifica quais movimentos são seguros (não batem imediatamente)
        safe_moves = []
        for move_name in possible_moves:
            nx, ny = head_grid
            if move_name == "up":
                ny -= 1
            elif move_name == "down":
                ny += 1
            elif move_name == "left":
                nx -= 1
            elif move_name == "right":
                nx += 1

            # Dentro do tabuleiro e não no corpo
            if (0 <= nx < grid_w and 0 <= ny < grid_h and
                (nx, ny) not in body_grid):
                safe_moves.append(move_name)

        # === ESTADO MUITO MAIS RICO PARA O LAYA ===
        state = {
            "description": "Você está controlando uma cobra no jogo Snake.",
            "board_size": f"{grid_w}x{grid_h}",
            "head_position": f"({head_grid[0]}, {head_grid[1]})",
            "food_position": f"({food_grid[0]}, {food_grid[1]})",
            "food_relative": {
                "dx": dx,
                "dy": dy,
                "horizontal": "direita" if dx > 0 else "esquerda" if dx < 0 else "mesma coluna",
                "vertical": "baixo" if dy > 0 else "cima" if dy < 0 else "mesma linha"
            },
            "current_direction": list(self.direction_map.keys())[list(self.direction_map.values()).index(current_dir)],
            "snake_length": len(body),
            "safe_moves": safe_moves if safe_moves else possible_moves,
            "possible_moves": possible_moves,
            "body_near_head": body_grid[1:6]  # segmentos próximos
        }

        # Pergunta mais precisa
        questions = {
            "next_move": {
                "type": "choice",
                "instructions": (
                    "Escolha a melhor direção para a cobra. "
                    "Priorize nesta ordem: "
                    "0. Aumentar o snake_length."
                    "1. Não morrer (usar apenas movimentos seguros se existirem), "
                    "2. Reduzir a distância até a comida, "
                    "3. Evitar ficar presa."
                ),
                "criteria": {
                    "up": "mover para cima",
                    "down": "mover para baixo",
                    "left": "mover para a esquerda",
                    "right": "mover para a direita"
                }
            }
        }

        try:
            result = self.agent.predict(state, questions)
            choice = result["answers"]["next_move"]["choice"]

            # Se o Laya escolher um movimento inseguro e existir movimento seguro, força um seguro
            if safe_moves and choice not in safe_moves:
                choice = safe_moves[0]

            return self.direction_map.get(choice, current_dir)

        except Exception as e:
            print(f"Erro no Laya: {e}")
            # Fallback: tenta um movimento seguro
            if safe_moves:
                return self.direction_map[safe_moves[0]]
            return current_dir
