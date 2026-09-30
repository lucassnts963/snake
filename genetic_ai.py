# genetic_ai.py
import copy
import os
import pickle
import random
from collections import deque
from multiprocessing import Pool, cpu_count

import numpy as np

from config import Configuration

config = Configuration()

# Direções absolutas: 0=UP 1=DOWN 2=LEFT 3=RIGHT (no jogo real: 1..4, mesma ordem)
DIRS = [(0, -1), (0, 1), (-1, 0), (1, 0)]
TURN_RIGHT = {0: 3, 3: 1, 1: 2, 2: 0}
TURN_LEFT = {0: 2, 2: 1, 1: 3, 3: 0}

# Ações relativas à cabeça: 0=seguir reto, 1=virar à direita, 2=virar à esquerda
INPUT_SIZE = 11
OUTPUT_SIZE = 3


def apply_action(direction, action):
    if action == 1:
        return TURN_RIGHT[direction]
    if action == 2:
        return TURN_LEFT[direction]
    return direction


def build_state(head, occupied, food, direction, width, height):
    """Estado (11 entradas) compartilhado entre o treino e o jogo real.

    Só usa informação relativa/binária, então funciona em qualquer tamanho de tabuleiro:
    perigo (reto, direita, esquerda) + direção atual (one-hot) + onde a comida está.
    """
    hx, hy = head

    def blocked(d):
        dx, dy = DIRS[d]
        x, y = hx + dx, hy + dy
        return int(not (0 <= x < width and 0 <= y < height) or (x, y) in occupied)

    fx, fy = food
    return [
        blocked(direction),
        blocked(TURN_RIGHT[direction]),
        blocked(TURN_LEFT[direction]),
        int(direction == 0), int(direction == 1), int(direction == 2), int(direction == 3),
        int(fx < hx), int(fx > hx), int(fy < hy), int(fy > hy),
    ]


# ====================== REDE NEURAL ======================
class NeuralNetwork:
    def __init__(self, input_size=INPUT_SIZE, hidden1=16, hidden2=12, output_size=OUTPUT_SIZE):
        self.w1 = np.random.randn(input_size, hidden1) * np.sqrt(2 / input_size)
        self.b1 = np.zeros(hidden1)
        self.w2 = np.random.randn(hidden1, hidden2) * np.sqrt(2 / hidden1)
        self.b2 = np.zeros(hidden2)
        self.w3 = np.random.randn(hidden2, output_size) * np.sqrt(2 / hidden2)
        self.b3 = np.zeros(output_size)

    def forward(self, x):
        """Retorna os logits (argmax é o mesmo que o do softmax, então não precisa dele)."""
        a1 = np.maximum(0, np.asarray(x, dtype=float) @ self.w1 + self.b1)
        a2 = np.maximum(0, a1 @ self.w2 + self.b2)
        return a2 @ self.w3 + self.b3

    def get_weights(self):
        return [self.w1.copy(), self.b1.copy(), self.w2.copy(), self.b2.copy(), self.w3.copy(), self.b3.copy()]

    def set_weights(self, weights):
        self.w1, self.b1, self.w2, self.b2, self.w3, self.b3 = [np.array(w, dtype=float) for w in weights]

    def mutate(self, rate=0.1, strength=0.2):
        for w in (self.w1, self.b1, self.w2, self.b2, self.w3, self.b3):
            mask = np.random.random(w.shape) < rate
            w += mask * np.random.randn(*w.shape) * strength


# ====================== AGENTE ======================
class Agent:
    def __init__(self, brain=None):
        self.brain = brain if brain else NeuralNetwork()
        self.fitness = 0
        self.score = 0
        self.survived = False  # não perdeu em nenhuma partida da avaliação

    def decide(self, state):
        return int(np.argmax(self.brain.forward(state)))  # 0=reto 1=direita 2=esquerda


def save_agent(agent, path):
    np.savez(path, *agent.brain.get_weights())


def load_agent(path):
    data = np.load(path)
    weights = [data[f"arr_{i}"] for i in range(6)]
    brain = NeuralNetwork(weights[0].shape[0], weights[0].shape[1], weights[2].shape[1], weights[4].shape[1])
    brain.set_weights(weights)
    return Agent(brain)


# ====================== AMBIENTE MINIATURA ======================
class MiniSnake:
    def __init__(self, size=20, rng=None):
        self.size = size
        self.rng = rng or random.Random()
        self.reset()

    def reset(self):
        mid = self.size // 2
        self.snake = deque([(mid, mid), (mid - 1, mid), (mid - 2, mid)])
        self.occupied = set(self.snake)
        self.direction = 3  # RIGHT
        self.score = 0
        self.steps = 0
        self.steps_without_food = 0
        self.shaping = 0.0
        self.alive = True
        self.won = False
        self.food = self._spawn_food()

    def _spawn_food(self):
        if len(self.occupied) >= self.size * self.size:
            self.alive = False  # tabuleiro cheio: não dá para perder mais
            self.won = True
            return (0, 0)
        while True:
            pos = (self.rng.randrange(self.size), self.rng.randrange(self.size))
            if pos not in self.occupied:
                return pos

    def get_state(self):
        return build_state(self.snake[0], self.occupied, self.food, self.direction, self.size, self.size)

    def step(self, action):
        self.direction = apply_action(self.direction, action)
        hx, hy = self.snake[0]
        dx, dy = DIRS[self.direction]
        new_head = (hx + dx, hy + dy)

        if not (0 <= new_head[0] < self.size and 0 <= new_head[1] < self.size) or new_head in self.occupied:
            self.alive = False
            return

        fx, fy = self.food
        old_dist = abs(fx - hx) + abs(fy - hy)

        self.snake.appendleft(new_head)
        self.occupied.add(new_head)
        self.steps += 1
        self.steps_without_food += 1

        if new_head == self.food:
            self.score += 1
            self.steps_without_food = 0
            self.food = self._spawn_food()
        else:
            self.occupied.discard(self.snake.pop())
            new_dist = abs(fx - new_head[0]) + abs(fy - new_head[1])
            self.shaping += 1.0 if new_dist < old_dist else -1.5  # incentiva ir em direção à comida

        # Morre de fome (evita loops infinitos)
        if self.steps_without_food > 100 + 4 * len(self.snake):
            self.alive = False

    def fitness(self):
        return self.score * 100 + self.score ** 2 * 10 + self.shaping + self.steps * 0.02


def _run_episode(brain, board_size, seed, max_steps):
    """Joga até perder. Se max_steps for dado, chegar nele sem perder conta como 'sobreviveu'."""
    env = MiniSnake(board_size, random.Random(seed))
    while env.alive and (max_steps is None or env.steps < max_steps):
        env.step(int(np.argmax(brain.forward(env.get_state()))))
    return env.fitness(), env.score, env.alive or env.won


def _run_many(job):
    """Roda um cérebro em várias sementes. Função de módulo para funcionar no multiprocessing."""
    weights, board_size, seeds, max_steps = job
    brain = NeuralNetwork()
    brain.set_weights(weights)
    results = [_run_episode(brain, board_size, s, max_steps) for s in seeds]
    fits, scores, survived = zip(*results)
    return float(np.mean(fits)), float(np.mean(scores)), max(scores), all(survived)


# ====================== ALGORITMO GENÉTICO ======================
class GeneticTrainer:
    def __init__(self, population_size=150, board_size=20, episodes=3, max_steps=None, workers=None):
        # max_steps=None: cada indivíduo joga até perder (sem limite de tempo).
        # max_steps=N: quem aguentar N passos sem perder é considerado "sobrevivente".
        self.pop_size = population_size
        self.board_size = board_size
        self.episodes = episodes
        self.max_steps = max_steps
        self.workers = workers if workers is not None else max(1, min(cpu_count() - 1, 8))
        self.pool = Pool(self.workers) if self.workers > 1 else None

        self.population = [Agent() for _ in range(population_size)]
        self.last_ranked = []
        self.generation = 0
        self.best_fitness = 0
        self.avg_fitness = 0
        self.record_score = 0
        self.champion = None
        self.champion_value = -1.0

    def close(self):
        if self.pool:
            self.pool.close()
            self.pool.join()
            self.pool = None

    def _evaluate(self, agents, seeds):
        jobs = [(a.brain.get_weights(), self.board_size, seeds, self.max_steps) for a in agents]
        if self.pool:
            return self.pool.map(_run_many, jobs, chunksize=max(1, len(jobs) // (self.workers * 4)))
        return [_run_many(j) for j in jobs]

    def evolve(self):
        # Todos jogam nas mesmas sementes, então a comparação entre eles é justa
        seeds = [random.randrange(2 ** 31) for _ in range(self.episodes)]
        for agent, (fit, _, best_score, survived) in zip(self.population, self._evaluate(self.population, seeds)):
            agent.fitness = fit
            agent.score = best_score
            agent.survived = survived

        self.population.sort(key=lambda a: a.fitness, reverse=True)
        self.last_ranked = list(self.population)
        best = self.population[0]
        self.best_fitness = best.fitness
        self.avg_fitness = sum(a.fitness for a in self.population) / self.pop_size
        self.record_score = max(self.record_score, best.score)

        # Elitismo: os melhores passam intactos
        elite_count = max(4, self.pop_size // 10)
        new_pop = [copy.deepcopy(a) for a in self.population[:elite_count]]

        while len(new_pop) < self.pop_size:
            child = self._crossover(self._tournament(), self._tournament())
            child.brain.mutate(rate=0.1, strength=0.2)
            new_pop.append(child)

        self.population = new_pop
        self.generation += 1
        return best

    def update_champion(self, candidates, episodes=20):
        """Reavalia os candidatos numa bateria maior de partidas e guarda o melhor de verdade."""
        seeds = [random.randrange(2 ** 31) for _ in range(episodes)]
        for agent, (fit, mean_score, _, _) in zip(candidates, self._evaluate(candidates, seeds)):
            if fit > self.champion_value:
                self.champion_value = fit
                self.champion = copy.deepcopy(agent)
                self.champion.score = mean_score
        return self.champion

    def find_unbeatable(self, episodes=20):
        """Procura, entre os que não perderam na avaliação, um que também não perde numa bateria maior
        de partidas novas (evita parar por sorte). Retorna o agente ou None."""
        survivors = [a for a in self.last_ranked if a.survived][:5]
        if not survivors:
            return None
        seeds = [random.randrange(2 ** 31) for _ in range(episodes)]
        for agent, (fit, mean_score, _, survived) in zip(survivors, self._evaluate(survivors, seeds)):
            if survived:
                self.champion = copy.deepcopy(agent)
                self.champion.score = mean_score
                self.champion_value = fit
                return self.champion
        return None

    def _tournament(self, k=4):
        return max(random.sample(self.population, k), key=lambda a: a.fitness)

    def _crossover(self, p1, p2):
        child = Agent()
        new_w = []
        for a, b in zip(p1.brain.get_weights(), p2.brain.get_weights()):
            new_w.append(np.where(np.random.rand(*a.shape) > 0.5, a, b))
        child.brain.set_weights(new_w)
        return child

    # ---------- persistência (permite retomar o treino de onde parou) ----------
    def save_state(self, path):
        state = {
            "generation": self.generation,
            "record_score": self.record_score,
            "champion_value": self.champion_value,
            "champion": self.champion.brain.get_weights() if self.champion else None,
            "champion_score": self.champion.score if self.champion else 0,
            "population": [a.brain.get_weights() for a in self.population],
        }
        with open(path, "wb") as f:
            pickle.dump(state, f)

    def load_state(self, path):
        with open(path, "rb") as f:
            state = pickle.load(f)
        self.generation = state["generation"]
        self.record_score = state["record_score"]
        self.champion_value = state["champion_value"]
        if state["champion"] is not None:
            self.champion = Agent()
            self.champion.brain.set_weights(state["champion"])
            self.champion.score = state["champion_score"]
        self.population = []
        for weights in state["population"][: self.pop_size]:
            agent = Agent()
            agent.brain.set_weights(weights)
            self.population.append(agent)
        while len(self.population) < self.pop_size:  # população pedida maior que a salva
            self.population.append(self._mutated_clone(self.population[0], rate=0.3, strength=0.3))

    def seed_from_agent(self, agent):
        """Recomeça a partir de um único agente (ex.: o best_snake.npz): ele + variações dele."""
        self.population = [copy.deepcopy(agent)]
        while len(self.population) < self.pop_size:
            self.population.append(self._mutated_clone(agent, rate=0.15, strength=0.2))

    @staticmethod
    def _mutated_clone(agent, rate, strength):
        clone = copy.deepcopy(agent)
        clone.brain.mutate(rate=rate, strength=strength)
        return clone

    def train(self, generations=100, save_path="best_snake.npz", state_path="best_snake_state.pkl",
              checkpoint_every=10, on_generation=None, stop_when_unbeatable=True):
        """Treina até `generations` gerações, valida periodicamente e salva o melhor agente (save_path)
        e o estado completo (state_path) para o treino poder ser retomado.
        Para antes se surgir um agente que não perde mais (ver find_unbeatable)."""
        unbeatable = False
        try:
            for i in range(1, generations + 1):
                best = self.evolve()
                print(f"Geração {self.generation:4d} | melhor score: {best.score:3d} | "
                      f"fitness: {best.fitness:8.1f} | média: {self.avg_fitness:8.1f} | recorde: {self.record_score}")

                if stop_when_unbeatable and self.find_unbeatable():
                    print(f"  ** Um agente não perde mais (score médio {self.champion.score:.1f} "
                          f"em 20 partidas novas). Parando o treino. **")
                    unbeatable = True
                    break

                if i % checkpoint_every == 0:
                    self._checkpoint(save_path, state_path)

                if on_generation and on_generation(self) is False:
                    break
        finally:
            # roda também em Ctrl+C / janela fechada, então nunca perde o progresso
            if unbeatable:
                save_agent(self.champion, save_path)  # mantém exatamente o agente validado
                self.save_state(state_path)
                print(f"  -> agente salvo em {save_path} (geração {self.generation})")
            elif self.last_ranked:
                self._checkpoint(save_path, state_path)
            self.close()
        return self.champion

    def _checkpoint(self, save_path, state_path):
        candidates = self.last_ranked[:5] + ([self.champion] if self.champion else [])
        champ = self.update_champion(candidates)
        save_agent(champ, save_path)
        self.save_state(state_path)
        print(f"  -> checkpoint salvo (geração {self.generation}, score médio do campeão: {champ.score:.1f})")


# ====================== PAINEL VISUAL DE TREINAMENTO ======================
class TrainingPanel:
    """Mostra os melhores agentes de cada geração jogando (opcional, deixa o treino mais lento)."""

    def __init__(self, trainer, rows=3, cols=5, cell_size=9):
        import pygame
        self.pg = pygame
        self.trainer = trainer
        self.rows, self.cols, self.cell = rows, cols, cell_size
        self.board = trainer.board_size

        pygame.init()
        w = cols * (self.board * cell_size + 10) + 20
        h = rows * (self.board * cell_size + 28) + 70
        self.screen = pygame.display.set_mode((w, h))
        pygame.display.set_caption("Neuroevolução - Snake Learning")
        self.font = pygame.font.SysFont("consolas", 16)
        self.small = pygame.font.SysFont("consolas", 12)
        self.clock = pygame.time.Clock()

    def show_generation(self):
        """Os melhores da geração jogam até perder (ou até max_steps, se houver).
        ESPAÇO pula para a próxima geração. Retorna False se o usuário fechou a janela."""
        pg, t = self.pg, self.trainer
        agents = t.last_ranked[: self.rows * self.cols]
        envs = [MiniSnake(self.board) for _ in agents]

        frame = 0
        while t.max_steps is None or frame < t.max_steps:
            frame += 1
            for event in pg.event.get():
                if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                    return False
                if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                    return True

            self.screen.fill((20, 20, 30))
            title = self.font.render(
                f"Geração: {t.generation} | Fitness: {t.best_fitness:.0f} | "
                f"Média: {t.avg_fitness:.0f} | Recorde: {t.record_score}", True, (220, 220, 255))
            self.screen.blit(title, (15, 10))

            for idx, (agent, env) in enumerate(zip(agents, envs)):
                if env.alive:
                    env.step(agent.decide(env.get_state()))
                r, c = divmod(idx, self.cols)
                ox = 15 + c * (self.board * self.cell + 10)
                oy = 40 + r * (self.board * self.cell + 28)
                pg.draw.rect(self.screen, (40, 40, 55), (ox, oy, self.board * self.cell, self.board * self.cell))
                fx, fy = env.food
                pg.draw.rect(self.screen, (220, 60, 60), (ox + fx * self.cell, oy + fy * self.cell, self.cell - 1, self.cell - 1))
                for j, (x, y) in enumerate(env.snake):
                    color = (80, 220, 120) if j == 0 else (50, 160, 90)
                    if not env.alive:
                        color = (120, 60, 60)
                    pg.draw.rect(self.screen, color, (ox + x * self.cell, oy + y * self.cell, self.cell - 1, self.cell - 1))
                txt = self.small.render(str(env.score), True, (200, 200, 200))
                self.screen.blit(txt, (ox, oy + self.board * self.cell + 2))

            pg.display.flip()
            self.clock.tick(120)
            if not any(e.alive for e in envs):
                break
        return True

    def close(self):
        self.pg.quit()


# ====================== PLAYER PARA O JOGO REAL ======================
class GeneticPlayer:
    """Usado pelo game.py: converte o estado do jogo real e devolve a direção (1=UP 2=DOWN 3=LEFT 4=RIGHT)."""

    def __init__(self, agent=None):
        self.agent = agent

    @classmethod
    def load(cls, path="best_snake.npz"):
        if not os.path.exists(path):
            print(f"[genetic_ai] '{path}' não encontrado. Rode 'python train.py' primeiro.")
            return cls(None)
        print(f"[genetic_ai] cérebro carregado de {path}")
        return cls(load_agent(path))

    def decide(self, snake, food):
        if self.agent is None:
            return snake.direction

        size = config.size_rect
        width = config.screen_size[0] // size
        height = config.screen_size[1] // size

        head = (snake.body[0][0] // size, snake.body[0][1] // size)
        occupied = {(x // size, y // size) for x, y in snake.body}
        food_g = (food.position[0] // size, food.position[1] // size)
        direction = snake.direction - 1  # 1..4 -> 0..3

        action = self.agent.decide(build_state(head, occupied, food_g, direction, width, height))
        return apply_action(direction, action) + 1
