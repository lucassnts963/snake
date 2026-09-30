# train.py
import argparse
import os

from genetic_ai import GeneticTrainer, TrainingPanel, load_agent


def main():
    parser = argparse.ArgumentParser(description="Treina a cobra com algoritmo genético (retoma de onde parou)")
    parser.add_argument("--generations", type=int, default=100, help="quantas gerações rodar NESTA execução")
    parser.add_argument("--population", type=int, default=150)
    parser.add_argument("--board", type=int, default=20, help="tamanho do tabuleiro de treino")
    parser.add_argument("--survive-steps", type=int, default=0,
                        help="0 (padrão) = cada indivíduo joga até perder, sem limite de tempo. "
                             "N > 0 = quem aguentar N passos sem perder nas 20 partidas de validação "
                             "'não perde mais' e o treino para")
    parser.add_argument("--workers", type=int, default=None, help="processos paralelos (1 = sem paralelismo)")
    parser.add_argument("--out", default="best_snake.npz", help="melhor agente (usado pelo game.py)")
    parser.add_argument("--state", default="best_snake_state.pkl", help="estado completo para retomar o treino")
    parser.add_argument("--fresh", action="store_true",
                        help="começa a aprender do zero (ignora o que foi salvo; sobrescreve os arquivos salvos)")
    parser.add_argument("--headless", action="store_true",
                        help="sem painel visual (treina bem mais rápido)")
    args = parser.parse_args()

    trainer = GeneticTrainer(population_size=args.population, board_size=args.board, workers=args.workers,
                             max_steps=args.survive_steps or None)

    if args.fresh:
        print("Começando a aprender do zero.")
    else:
        if os.path.exists(args.state):
            trainer.load_state(args.state)
            print(f"Retomando da geração {trainer.generation} (recorde {trainer.record_score}) — {args.state}")
        elif os.path.exists(args.out):
            trainer.seed_from_agent(load_agent(args.out))
            print(f"Sem estado salvo; semeando a população com o agente de {args.out}")

    panel = None if args.headless else TrainingPanel(trainer)
    on_generation = (lambda t: panel.show_generation()) if panel else None

    trainer.train(generations=args.generations, save_path=args.out, state_path=args.state,
                  on_generation=on_generation)

    if panel:
        panel.close()
    print(f"Melhor agente salvo em {args.out}. Agora rode: python game.py")


if __name__ == "__main__":
    main()
